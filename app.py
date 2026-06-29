import json
import math
import os
import random
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    serial = None

HOST = "127.0.0.1"
PORT = 8766
BAUD = 9600


def resource_path(relative_path):
    """Resuelve recursos tanto en desarrollo como dentro del ejecutable."""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


STATIC_DIR = resource_path("static")

state_lock = threading.Lock()
serial_lock = threading.Lock()
shutdown = threading.Event()
serial_connection = None
simulation_enabled = True
state = {
    "distance": 35.0,
    "valid": True,
    "stable": True,
    "spread": 0.3,
    "connected": False,
    "simulation": True,
    "port": None,
    "timestamp": time.time(),
}


class ThreadingServer(ThreadingMixIn, HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def do_GET(self):
        if self.path == "/api/ports":
            return self.send_ports()
        if self.path == "/api/state":
            return self.send_state()
        if self.path == "/stream":
            return self.send_stream()
        if self.path in ("/", "/index.html"):
            return self.send_file("index.html")
        return self.send_file(self.path.lstrip("/"))

    def do_POST(self):
        if self.path == "/api/serial":
            return self.serial_control()
        if self.path == "/api/simulation":
            return self.simulation_control()
        self.send_error(404)

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length)) if length else {}

    def send_json(self, payload, status=200):
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def send_ports(self):
        if serial is None:
            return self.send_json({"ports": [], "serialAvailable": False})
        ports = [
            {"port": item.device, "description": item.description or item.device}
            for item in serial.tools.list_ports.comports()
        ]
        self.send_json({"ports": ports, "serialAvailable": True})

    def send_state(self):
        with state_lock:
            snapshot = dict(state)
        self.send_json(snapshot)

    def send_stream(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        try:
            while not shutdown.is_set():
                with state_lock:
                    payload = json.dumps(state)
                self.wfile.write(f"data: {payload}\n\n".encode("utf-8"))
                self.wfile.flush()
                time.sleep(0.1)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def serial_control(self):
        body = self.read_json()
        action = body.get("action")
        if action == "connect":
            ok, message = open_serial(body.get("port", ""))
            return self.send_json({"ok": ok, "message": message}, 200 if ok else 400)
        if action == "disconnect":
            close_serial()
            return self.send_json({"ok": True})
        self.send_json({"ok": False, "message": "Acción desconocida"}, 400)

    def simulation_control(self):
        global simulation_enabled
        enabled = bool(self.read_json().get("enabled", False))
        simulation_enabled = enabled
        if enabled:
            close_serial()
        with state_lock:
            state["simulation"] = enabled
        self.send_json({"ok": True, "enabled": enabled})

    def send_file(self, relative_path):
        safe_path = os.path.abspath(os.path.join(STATIC_DIR, relative_path))
        if not safe_path.startswith(STATIC_DIR) or not os.path.isfile(safe_path):
            return self.send_error(404)
        mime = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".svg": "image/svg+xml",
            ".bmp": "image/bmp",
        }.get(os.path.splitext(safe_path)[1], "application/octet-stream")
        with open(safe_path, "rb") as file:
            content = file.read()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(content)


def open_serial(port_name):
    global serial_connection, simulation_enabled
    if serial is None:
        return False, "Falta instalar pyserial"
    if not port_name:
        return False, "Seleccioná un puerto COM"
    with serial_lock:
        try:
            if serial_connection and serial_connection.is_open:
                serial_connection.close()
            serial_connection = serial.Serial(port_name, BAUD, timeout=0.2)
            time.sleep(1.8)
            serial_connection.reset_input_buffer()
            simulation_enabled = False
            with state_lock:
                state.update(connected=True, simulation=False, port=port_name)
            return True, "Arduino conectado"
        except Exception as exc:
            serial_connection = None
            return False, f"No se pudo abrir {port_name}: {exc}"


def close_serial():
    global serial_connection
    with serial_lock:
        try:
            if serial_connection and serial_connection.is_open:
                serial_connection.close()
        finally:
            serial_connection = None
            with state_lock:
                state.update(connected=False, port=None)


def serial_worker():
    while not shutdown.is_set():
        with serial_lock:
            connection = serial_connection
        if connection and connection.is_open:
            try:
                raw = connection.readline().decode("utf-8", errors="replace").strip()
                if raw:
                    measurement = json.loads(raw)
                    with state_lock:
                        state.update(
                            distance=measurement.get("distance"),
                            valid=bool(measurement.get("valid")),
                            stable=bool(measurement.get("stable")),
                            spread=float(measurement.get("spread", 0)),
                            timestamp=time.time(),
                            connected=True,
                            simulation=False,
                        )
            except (json.JSONDecodeError, ValueError):
                pass
            except Exception:
                close_serial()
        else:
            time.sleep(0.05)


def simulation_worker():
    phase = 0.0
    while not shutdown.is_set():
        if simulation_enabled:
            phase += 0.045
            distance = 46 + 27 * math.sin(phase) + random.uniform(-0.15, 0.15)
            with state_lock:
                state.update(
                    distance=round(distance, 1), valid=True, stable=True,
                    spread=0.4, connected=False, simulation=True,
                    port=None, timestamp=time.time(),
                )
        time.sleep(0.1)


if __name__ == "__main__":
    threading.Thread(target=serial_worker, daemon=True).start()
    threading.Thread(target=simulation_worker, daemon=True).start()
    url = f"http://{HOST}:{PORT}"
    try:
        server = ThreadingServer((HOST, PORT), Handler)
    except OSError:
        # Si ya existe una instancia, abrir la interfaz existente y terminar.
        webbrowser.open(url)
        raise SystemExit(0)
    print(f"Regla Digital disponible en {url}")
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        shutdown.set()
        close_serial()
        server.server_close()
