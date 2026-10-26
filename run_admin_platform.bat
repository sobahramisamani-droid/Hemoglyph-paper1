@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Hemoglyph Sentinel - Executive CDS Admin AND Licensing Platform
color 0b

echo ============================================================
echo   HEMOGLYPH SENTINEL -- ADMIN COMMAND AND LICENSE PLATFORM
echo   Military-Grade RSA-4096 Cryptographic Management Suite
echo ============================================================
echo.

REM Activate virtual environment if available
if defined VIRTUAL_ENV goto :VENV_OK
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    goto :VENV_OK
)
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    goto :VENV_OK
)
if exist ..\.venv\Scripts\activate.bat (
    call ..\.venv\Scripts\activate.bat
    goto :VENV_OK
)
:VENV_OK

echo [*] Launching Sentinel Admin Platform on port 8090...
echo [*] Web Dashboard URL: http://127.0.0.1:8090
echo.

REM Automatically launch browser to the dashboard
start http://127.0.0.1:8090

REM Start Python Server on all interfaces (0.0.0.0)
python admin_platform.py --host 0.0.0.0 --port 8090
pause
