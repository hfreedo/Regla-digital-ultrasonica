const $ = (selector) => document.querySelector(selector);
const valueEl = $("#distanceValue");
const statusEl = $("#measurementStatus");
const targetEl = $("#target");
const beamEl = $("#beamFill");
const referenceMarker = $("#referenceMarker");
const maxDistance = 100;

let sensorState = { distance: 35, valid: true, stable: true, simulation: true, connected: false };
let displayedDistance = 35;
let frozen = false;
let frozenDistance = null;
let referenceDistance = null;
let challengeTarget = null;
let toastTimer;

function buildRuler() {
  const ruler = $("#ruler");
  for (let i = 0; i <= 100; i++) {
    const tick = document.createElement("div");
    tick.className = `tick ${i % 10 === 0 ? "major" : i % 5 === 0 ? "medium" : ""}`;
    tick.style.left = `${i}%`;
    if (i % 10 === 0) {
      const label = document.createElement("label");
      label.textContent = i;
      tick.appendChild(label);
    }
    ruler.appendChild(tick);
  }
}

function formatDistance(value) {
  return Number(value).toFixed(1).replace(".", ",");
}

function renderMeasurement() {
  if (!frozen && sensorState.valid && sensorState.distance != null) {
    displayedDistance += (sensorState.distance - displayedDistance) * 0.22;
  }

  if (!sensorState.valid || sensorState.distance == null) {
    valueEl.textContent = "— — —";
    statusEl.className = "measurement-status error";
    statusEl.innerHTML = "<span></span> OBJETO NO DETECTADO";
    targetEl.style.opacity = "0";
    beamEl.style.width = "0%";
  } else {
    const percent = Math.max(2, Math.min(100, displayedDistance / maxDistance * 100));
    valueEl.textContent = formatDistance(displayedDistance);
    targetEl.style.left = `${percent}%`;
    targetEl.style.opacity = "1";
    beamEl.style.width = `${percent}%`;
    if (displayedDistance < 3) {
      statusEl.className = "measurement-status warning";
      statusEl.innerHTML = "<span></span> OBJETO DEMASIADO CERCA";
    } else if (!sensorState.stable) {
      statusEl.className = "measurement-status warning";
      statusEl.innerHTML = "<span></span> ESTABILIZANDO LECTURA";
    } else {
      statusEl.className = "measurement-status stable";
      statusEl.innerHTML = "<span></span> MEDICIÓN ESTABLE";
    }
  }

  if (referenceDistance != null && sensorState.valid) {
    const difference = sensorState.distance - referenceDistance;
    $("#comparisonValue").textContent = `${formatDistance(referenceDistance)} cm / ${difference >= 0 ? "+" : ""}${formatDistance(difference)} cm`;
  }
  updateChallenge();
  requestAnimationFrame(renderMeasurement);
}

function updateConnection(state) {
  const dot = $("#connectionDot");
  const text = $("#connectionText");
  if (state.connected) {
    text.textContent = `ARDUINO ${state.port || "CONECTADO"}`;
    dot.style.background = "var(--green)";
    dot.style.boxShadow = "0 0 12px var(--green)";
    $("#connectBtn").textContent = "DESCONECTAR ARDUINO";
  } else if (state.simulation) {
    text.textContent = "MODO SIMULACIÓN";
    dot.style.background = "var(--yellow)";
    dot.style.boxShadow = "0 0 12px var(--yellow)";
    $("#connectBtn").textContent = "CONECTAR ARDUINO";
  } else {
    text.textContent = "DESCONECTADO";
    dot.style.background = "var(--red)";
    dot.style.boxShadow = "0 0 12px var(--red)";
  }
}

const events = new EventSource("/stream");
events.onmessage = (event) => {
  sensorState = JSON.parse(event.data);
  updateConnection(sensorState);
};
events.onerror = () => {
  $("#connectionText").textContent = "SERVIDOR SIN RESPUESTA";
};

function toast(message) {
  const element = $("#toast");
  element.textContent = message;
  element.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => element.classList.remove("show"), 2400);
}

$("#freezeBtn").addEventListener("click", () => {
  if (!sensorState.valid) return toast("No hay una medición válida para capturar");
  if (!frozen) {
    frozen = true;
    frozenDistance = displayedDistance;
    $("#frozenValue").textContent = `${formatDistance(frozenDistance)} cm`;
    $("#freezeBtn b").textContent = "CONTINUAR";
    $("#freezeBtn small").textContent = "Reanudar medición";
    document.body.classList.add("frozen");
  } else {
    frozen = false;
    $("#freezeBtn b").textContent = "CONGELAR";
    $("#freezeBtn small").textContent = "Capturar lectura";
    document.body.classList.remove("frozen");
  }
});

$("#referenceBtn").addEventListener("click", () => {
  if (!sensorState.valid) return toast("No hay una medición válida para usar como referencia");
  referenceDistance = sensorState.distance;
  referenceMarker.style.display = "block";
  referenceMarker.style.left = `${Math.min(100, referenceDistance)}%`;
  toast(`Referencia guardada en ${formatDistance(referenceDistance)} cm`);
});

$("#challengeBtn").addEventListener("click", () => {
  challengeTarget = Math.round(10 + Math.random() * 80);
  $("#challengeLabel").textContent = `OBJETIVO: ${challengeTarget} cm`;
  toast(`Desafío iniciado: colocá el objeto a ${challengeTarget} cm`);
});

function updateChallenge() {
  if (challengeTarget == null || !sensorState.valid) return;
  const difference = sensorState.distance - challengeTarget;
  const abs = Math.abs(difference);
  const el = $("#challengeValue");
  if (abs <= 1) {
    el.textContent = "¡OBJETIVO ALCANZADO!";
    el.style.color = "var(--green)";
  } else {
    el.textContent = difference > 0 ? `Acercar ${formatDistance(abs)} cm` : `Alejar ${formatDistance(abs)} cm`;
    el.style.color = "var(--yellow)";
  }
}

function setPanel(open) {
  $("#settingsPanel").classList.toggle("open", open);
  $("#overlay").classList.toggle("open", open);
  $("#settingsPanel").setAttribute("aria-hidden", String(!open));
  $("#settingsBtn").setAttribute("aria-expanded", String(open));
}
$("#settingsBtn").addEventListener("click", () => setPanel(true));
$("#closeSettings").addEventListener("click", () => setPanel(false));
$("#overlay").addEventListener("click", () => setPanel(false));
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && $("#settingsPanel").classList.contains("open")) {
    setPanel(false);
    $("#settingsBtn").focus();
  }
});
$("#fullscreenBtn").addEventListener("click", () => document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen());

async function refreshPorts() {
  const response = await fetch("/api/ports");
  const data = await response.json();
  const select = $("#portSelect");
  select.innerHTML = "";
  if (!data.serialAvailable) {
    select.innerHTML = '<option value="">Instalá pyserial</option>';
    return;
  }
  if (!data.ports.length) {
    select.innerHTML = '<option value="">No se encontraron puertos</option>';
    return;
  }
  data.ports.forEach(({port, description}) => select.add(new Option(`${port} — ${description}`, port)));
}
$("#refreshPorts").addEventListener("click", refreshPorts);

$("#connectBtn").addEventListener("click", async () => {
  const disconnecting = sensorState.connected;
  const response = await fetch("/api/serial", {
    method: "POST", headers: {"Content-Type": "application/json"},
    body: JSON.stringify(disconnecting ? {action: "disconnect"} : {action: "connect", port: $("#portSelect").value})
  });
  const result = await response.json();
  $("#connectionMessage").textContent = result.message || (disconnecting ? "Arduino desconectado." : "Arduino conectado.");
  if (!response.ok) toast(result.message || "No se pudo conectar");
});

$("#simulationBtn").addEventListener("click", async () => {
  await fetch("/api/simulation", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({enabled:true})});
  $("#connectionMessage").textContent = "Simulación activada. La medición se moverá automáticamente.";
  setPanel(false);
});

buildRuler();
refreshPorts();
renderMeasurement();
