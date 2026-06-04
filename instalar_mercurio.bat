@echo off
chcp 65001 >nul
title Instalador Mercurio Digital
cd /d "%~dp0"

echo ============================================================
echo   INSTALADOR DE ENTORNO - EL MERCURIO DIGITAL
echo ============================================================
echo.
echo   Carpeta detectada automaticamente: %~dp0
echo   (este instalador se ejecuta en la carpeta donde esta guardado)
echo.
echo   IMPORTANTE: NO hagas clic dentro de esta ventana mientras
echo   trabaja. Si el texto se congela, presiona ESC o ENTER.
echo.
pause
echo.

REM ── [1/6] Python ──
echo [1/6] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo   [ERROR] Python no esta instalado o no esta en el PATH.
    echo   Instalalo desde python.org marcando "Add Python to PATH".
    echo.
    pause & exit /b 1
)
for /f "tokens=*" %%v in ('python --version') do echo   OK: %%v
echo.

REM ── [2/6] Archivos del proyecto ──
echo [2/6] Verificando archivos del proyecto...
if not exist "main.py" (
    echo   [ERROR] No hay main.py en esta carpeta: %~dp0
    echo   Coloca este .bat en la carpeta donde estan main.py y requirements.txt.
    echo.
    pause & exit /b 1
)
if not exist "requirements.txt" (
    echo   [ERROR] No hay requirements.txt en esta carpeta.
    echo.
    pause & exit /b 1
)
echo   OK: main.py y requirements.txt presentes.
echo.

REM ── [3/6] Limpiar venv viejo ──
echo [3/6] Limpiando .venv anterior si existe...
if exist ".venv\" (
    rmdir /s /q ".venv"
    if exist ".venv\" (
        echo   [ERROR] No se pudo borrar el .venv viejo. Cierra CMD/editores
        echo   que lo usen y reintenta.
        pause & exit /b 1
    )
    echo   OK: .venv anterior eliminado.
) else (
    echo   OK: no habia .venv previo.
)
echo.

REM ── [4/6] Crear venv ──
echo [4/6] Creando entorno virtual... (1-3 min, NO toques la ventana)
python -m venv .venv
if not exist ".venv\Scripts\python.exe" (
    echo   Reintentando con --without-pip...
    if exist ".venv\" rmdir /s /q ".venv"
    python -m venv .venv --without-pip
    if not exist ".venv\Scripts\python.exe" (
        echo   [ERROR] No se pudo crear el .venv. Causa probable: antivirus.
        echo   Pausa la proteccion en tiempo real y reintenta.
        pause & exit /b 1
    )
    .venv\Scripts\python.exe -m ensurepip --upgrade
)
echo   OK: .venv creado.
echo.

REM ── [5/6] Instalar librerias (SIEMPRE con el python del venv) ──
echo [5/6] Instalando librerias en el .venv (varios min, requiere internet)...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo   [ERROR] Fallo la instalacion. Revisa internet y reintenta.
    pause & exit /b 1
)
echo   OK: librerias instaladas en el .venv.
echo.

REM ── [6/6] Chromium ──
echo [6/6] Descargando navegador Chromium...
.venv\Scripts\python.exe -m playwright install chromium
if errorlevel 1 (
    echo   [ERROR] No se pudo descargar Chromium. Revisa internet y reintenta.
    pause & exit /b 1
)
echo   OK: Chromium instalado.
echo.

REM ── Verificacion final: TODO carga desde el venv ──
echo Verificando que el pipeline completo carga desde el .venv...
.venv\Scripts\python.exe -c "import main; import fitz; import requests; import openai; import anthropic; print('   VERIFICACION OK: el pipeline y todas las librerias cargan.')"
if errorlevel 1 (
    echo   [ADVERTENCIA] La verificacion fallo. Algo no quedo bien.
    echo   Copia el mensaje de error de arriba para diagnosticarlo.
    pause & exit /b 1
)
echo.

echo ============================================================
echo   INSTALACION COMPLETADA CON EXITO
echo ============================================================
echo.
echo   Falta antes de la primera corrida:
echo     1. Copiar causas_ojv.xlsx (historial) a esta carpeta.
echo     2. En config.py pegar: ANTHROPIC_API_KEY, DEEPSEEK_API_KEY,
echo        MERCURIO_USER, MERCURIO_PASS.
echo.
echo   Luego ejecuta:  ejecutar_mercurio.bat
echo.
pause
