@echo off
chcp 65001 >nul
title Extractor El Mercurio Digital
echo ============================================================
echo   EXTRACTOR EL MERCURIO DIGITAL
echo ============================================================
echo.

cd /d "%~dp0"

REM Si se pasa una fecha como argumento, usarla. Si no, usar hoy.
if "%~1"=="" (
    REM Obtener fecha de hoy en formato YYYY-MM-DD via Python
    for /f %%i in ('python -c "from datetime import date; print(date.today())"') do set FECHA=%%i
) else (
    set FECHA=%~1
)

echo   Fecha edicion: %FECHA%
echo.
python main.py --fecha %FECHA%

echo.
echo ============================================================
echo   Ejecucion finalizada
echo ============================================================
echo.
pause
