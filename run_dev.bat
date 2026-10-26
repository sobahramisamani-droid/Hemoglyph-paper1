@echo off
setlocal
cd /d "%~dp0"
title Hemoglyph Python Dev Launcher
color 0a

echo ======================================================================
echo   HEMOGLYPH DEVELOPER RUNNER (AUTO DLL & PATH RESOLVER)
echo ======================================================================
echo.

REM 1. Locate Python executable in .venv or system
set PYTHON_EXE=
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
    set "VENV_DIR=%~dp0.venv"
) else if exist "%~dp0..\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0..\.venv\Scripts\python.exe"
    set "VENV_DIR=%~dp0..\.venv"
) else (
    set "PYTHON_EXE=python"
    set "VENV_DIR="
)

echo [*] Using Python: %PYTHON_EXE%

REM 2. Set clean sanitized PATH prioritizing venv Scripts, PySide6, and Windows System32
if defined VENV_DIR (
    set "PATH=%VENV_DIR%\Scripts;%VENV_DIR%\Lib\site-packages\PySide6;%VENV_DIR%\Lib\site-packages\shiboken6;C:\Windows\System32;C:\Windows"
)

echo [*] Launching Hemoglyph app.py...
echo.
"%PYTHON_EXE%" "%~dp0app.py"

if errorlevel 1 (
    echo.
    echo ======================================================================
    echo   [NOTICE] If you only want to test OCR Vision API, run:
    echo   test_ocr_api.bat
    echo ======================================================================
)

pause
