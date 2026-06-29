from pathlib import Path
import shutil
import subprocess
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
PACKAGE = ROOT / "release" / "ReglaDigitalPortable"
ZIP_PATH = ROOT / "ReglaDigitalPortable.zip"


def remove_within_root(path: Path) -> None:
    resolved = path.resolve()
    if ROOT.resolve() not in resolved.parents:
        raise RuntimeError(f"Ruta fuera del proyecto: {resolved}")
    if resolved.is_dir():
        shutil.rmtree(resolved)
    elif resolved.exists():
        resolved.unlink()


def main() -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onefile",
            "--noconsole",
            "--name",
            "ReglaDigital",
            "--add-data",
            f"{ROOT / 'static'};static",
            "--hidden-import",
            "serial.tools.list_ports",
            str(ROOT / "app.py"),
        ],
        cwd=ROOT,
        check=True,
    )

    remove_within_root(PACKAGE)
    PACKAGE.mkdir(parents=True)
    (PACKAGE / "firmware").mkdir()
    (PACKAGE / "docs").mkdir()

    shutil.copy2(DIST / "ReglaDigital.exe", PACKAGE / "ReglaDigital.exe")
    shutil.copy2(ROOT / "arduino" / "regla_digital" / "regla_digital.ino", PACKAGE / "firmware" / "regla_digital.ino")
    shutil.copy2(ROOT / "docs" / "LEEME_PRIMERO.md", PACKAGE / "LEEME_PRIMERO.md")
    shutil.copy2(ROOT / "docs" / "CONEXIONES.md", PACKAGE / "docs" / "CONEXIONES.md")
    shutil.copy2(ROOT / "LICENSE.md", PACKAGE / "LICENSE.md")

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for file in sorted(PACKAGE.rglob("*")):
            if file.is_file():
                archive.write(file, Path("ReglaDigitalPortable") / file.relative_to(PACKAGE))

    print(f"Ejecutable: {DIST / 'ReglaDigital.exe'}")
    print(f"Paquete: {ZIP_PATH}")


if __name__ == "__main__":
    main()
