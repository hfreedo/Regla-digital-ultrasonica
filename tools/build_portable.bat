@echo off
setlocal
cd /d "%~dp0.."

echo Instalando herramientas de empaquetado...
python -m pip install -r requirements-build.txt
if errorlevel 1 exit /b 1

echo Construyendo ReglaDigital.exe y el paquete portable...
python tools\build_portable.py
if errorlevel 1 exit /b 1

echo.
echo Paquete generado correctamente:
echo %cd%\ReglaDigitalPortable.zip
pause
