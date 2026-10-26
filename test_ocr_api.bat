@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Hemoglyph Vision OCR Diagnostic Tool
color 0b

echo ======================================================================
echo   HEMOGLYPH VISION OCR COMMAND-LINE DIAGNOSTIC TOOL
echo ======================================================================
echo.

set PYTHON_EXE=
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
) else if exist "%~dp0..\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0..\.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo [*] Python interpreter: %PYTHON_EXE%
echo [*] Testing Vision OCR API connection and diagnostics...
echo.

"%PYTHON_EXE%" "%~dp0test_ocr_api.py" %*

echo.
echo ======================================================================
pause
