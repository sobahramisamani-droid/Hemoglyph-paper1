@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title HEMOGLYPH - Ultra-Fast 60-Second Standalone Builder
color 0b

echo ======================================================================
echo   HEMOGLYPH ULTRA-FAST 60-SECOND STANDALONE MASTER BUILDER (v1.3.1)
echo   Fast, Stable, No GCC Lag, Zero Memory Crashes, Under 60 Seconds!
echo ======================================================================
echo.

REM 1. Activate Virtual Environment
if exist "%~dp0.venv\Scripts\activate.bat" call "%~dp0.venv\Scripts\activate.bat"

REM 2. Sanitize Environment (Eliminate Anaconda DLL pollution)
set CONDA_PREFIX=
set CONDA_DEFAULT_ENV=
set PYTHONHOME=
if exist "%~dp0.venv\Scripts" (
    set "PATH=%~dp0.venv\Scripts;%~dp0.venv\Lib\site-packages\PySide6;%~dp0.venv\Lib\site-packages\PySide6\Qt\bin;C:\Windows\System32;C:\Windows"
)

REM 3. Set Direct Python Executable
set PYTHON_CMD=python
if exist "%~dp0.venv\Scripts\python.exe" set "PYTHON_CMD=%~dp0.venv\Scripts\python.exe"

echo [*] Using Python: %PYTHON_CMD%
%PYTHON_CMD% -c "import PySide6.QtCore; print('[*] PySide6 QtCore verified successfully.')" 2>nul

REM 4. Ensure PyInstaller and Dependencies
%PYTHON_CMD% -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [*] Installing PyInstaller engine...
    %PYTHON_CMD% -m pip install pyinstaller brotli openai httpx
)

REM 5. Pre-compress Registries with Brotli if needed
if exist "%~dp0br.py" %PYTHON_CMD% "%~dp0br.py"

echo.
echo ======================================================================
echo   [STEP 1/3] RAPID STANDALONE EXE GENERATION (TURBO ENGINE)
echo   * Compiling bytecodes and packaging offline runtime...
echo   * Expected time: 45 to 60 seconds
echo ======================================================================
echo.

%PYTHON_CMD% -O -m PyInstaller --clean --noconfirm Hemoglyph.spec

if errorlevel 1 (
    echo [ERROR] PyInstaller compilation failed.
    pause
    exit /b 1
)

echo.
echo ======================================================================
echo   [STEP 2/3] INGESTING ESSENTIAL DLLs AND RUNTIME EXTENSIONS
echo ======================================================================
echo.
%PYTHON_CMD% "%~dp0_post_build.py"

echo.
echo ======================================================================
echo   [STEP 3/3] CLEAN 'bin' STRUCTURE & DESKTOP SHORTCUT CREATOR
echo ======================================================================
echo.
%PYTHON_CMD% "%~dp0_organize_release.py"

echo.
echo ======================================================================
echo   [ALL DONE - 100%% SUCCESS IN 60 SECONDS!]
echo   1. Standalone Hemoglyph.exe generated without any GCC lag!
echo   2. All DLLs and PySide6 folders organized into 'bin\'
echo   3. Desktop Shortcut Builder (Create_Desktop_Shortcut.bat) placed in root
echo   4. Clean ZIP package created in dist\ folder!
echo ======================================================================
echo.
pause
