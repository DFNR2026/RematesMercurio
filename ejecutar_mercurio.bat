@echo off
chcp 65001 >nul
title Extractor El Mercurio Digital
echo ============================================================
echo   EXTRACTOR EL MERCURIO DIGITAL
echo ============================================================
echo.

cd /d "%~dp0"

REM --- Activar entorno virtual local si existe ---
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
) else (
    echo [AVISO] No se encontro .venv en esta carpeta. Usando Python global.
    echo         Si falta alguna libreria, crea el entorno con:
    echo             python -m venv .venv ^&^& .venv\Scripts\activate.bat ^&^& pip install -r requirements.txt
    echo.
)

REM Uso:  doble clic = edicion de hoy
REM       ejecutar_mercurio.bat 2026-10-17              = una edicion
REM       ejecutar_mercurio.bat 2026-10-14 2026-10-17   = varias ediciones en un solo Excel
if "%~1"=="" (
    python main.py
) else if "%~2"=="" (
    echo   Edicion: %~1
    python main.py --fecha %~1
) else (
    echo   Ediciones: %~1 al %~2
    python main.py --fecha %~1 --fecha-fin %~2
)
set CODIGO=%ERRORLEVEL%

echo.
if "%CODIGO%"=="0" (
    echo ============================================================
    echo   Ejecucion finalizada. El informe esta en la carpeta "Informe final".
    echo ============================================================
) else if "%CODIGO%"=="2" (
    echo ############################################################
    echo   LA EDICION DE HOY TODAVIA NO ESTA PUBLICADA
    echo   Pruebe de nuevo en un rato.
    echo ############################################################
) else (
    echo ############################################################
    if "%CODIGO%"=="3" echo   ATENCION. NO SE PUDO LEER EL DIARIO. NO HAY INFORME.
    if "%CODIGO%"=="3" echo   Esto NO significa que hoy no haya remates.
    if "%CODIGO%"=="4" echo   ATENCION. EL INFORME PUEDE ESTAR INCOMPLETO.
    if "%CODIGO%"=="4" echo   Su nombre termina en INCOMPLETO. Arriba dice que paso.
    if "%CODIGO%"=="1" echo   ATENCION. EL PROGRAMA TUVO UN ERROR INESPERADO.
    echo ############################################################
    echo   QUE HACER
    echo   1. Revise que el computador tenga internet.
    echo   2. Espere unos 10 minutos y vuelva a hacer doble clic en este archivo.
    echo   3. Si dice que la edicion no esta disponible, pruebe mas tarde.
    echo   4. Si habla de la inteligencia artificial, puede faltar saldo. Avise a Diego.
    echo   5. Si falla dos veces seguidas, avise a Diego y enviele el archivo
    echo      mas nuevo de la carpeta logs.
    echo   6. Mientras tanto puede revisar los remates en El Mercurio,
    echo      Clasificados, seccion 1616.
    echo   Estos pasos tambien estan en QUE_HACER_SI_FALLA.txt
    echo ############################################################
)
echo.
pause
