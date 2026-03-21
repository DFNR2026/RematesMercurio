@echo off
chcp 65001 >nul
title Cronometro Mercurio
color 0A

echo ============================================================
echo   CRONOMETRO MERCURIO
echo   Iniciado: %date% %time:~0,8%
echo ============================================================
echo.
echo   Hora objetivo: 05:00 AM
echo   Si edicion no disponible: reintenta cada 30 min (max 6)
echo.
echo   Dejar esta ventana abierta.
echo   Presionar Ctrl+C para cancelar.
echo.
echo ============================================================
echo.

REM FASE 1: Si ya pasaron las 5am, esperar hasta medianoche
:ESPERAR_NOCHE
set HORA_ACTUAL=%time:~0,2%
set HORA_ACTUAL=%HORA_ACTUAL: =%

if %HORA_ACTUAL% GEQ 5 (
    echo   [%time:~0,8%] Ya pasaron las 05:00. Esperando hasta manana...
    timeout /t 600 /nobreak >nul
    goto ESPERAR_NOCHE
)

REM FASE 2: Es madrugada (0-4), esperar hasta las 5
:ESPERAR_5AM
set HORA_ACTUAL=%time:~0,2%
set HORA_ACTUAL=%HORA_ACTUAL: =%

if %HORA_ACTUAL% LSS 5 (
    echo   [%time:~0,8%] Esperando... faltan horas para las 05:00
    timeout /t 300 /nobreak >nul
    goto ESPERAR_5AM
)

REM FASE 3: Son las 5+, ejecutar
cd /d %~dp0

for /f %%i in ('python -c "from datetime import date; print(date.today())"') do set FECHA=%%i

echo.
echo ============================================================
echo   [%time:~0,8%] Son las 5 AM. Fecha objetivo: %FECHA%
echo ============================================================

set INTENTO=1
set MAX_INTENTOS=6

:REINTENTAR
echo.
echo   === Intento %INTENTO% de %MAX_INTENTOS% [%time:~0,8%] ===
echo.

python main.py --fecha %FECHA%

if %ERRORLEVEL%==2 (
    if %INTENTO% LSS %MAX_INTENTOS% (
        set /a INTENTO+=1
        echo.
        echo   [%time:~0,8%] Edicion del %FECHA% no disponible aun.
        echo   Reintentando en 30 minutos...
        timeout /t 1800 /nobreak >nul
        goto REINTENTAR
    ) else (
        echo.
        echo   [%time:~0,8%] Se agotaron los %MAX_INTENTOS% intentos.
        goto FIN
    )
) else (
    echo.
    echo   [%time:~0,8%] Ejecucion completada.
)

:FIN
echo.
echo ============================================================
echo   CRONOMETRO MERCURIO FINALIZADO
echo   %date% %time:~0,8%
echo ============================================================
echo.
pause
