@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title HEMOGLYPH 1.3.1 - clean setup and build
color 0b

echo ======================================================================
echo   HEMOGLYPH 1.3.1  -  CLEAN SETUP AND BUILD  -  one command, start to end
echo   1. find official python.org Python 3.11 or 3.12  - never conda
echo   2. create a fresh venv  .venv_official  - nothing else is deleted
echo   3. install exact dependencies  - PyPI, then Iranian mirror
echo   4. pre-flight checks
echo   5. Nuitka native build  - LITE mode, RAM-aware
echo   6. verify dist, create desktop shortcut
echo ======================================================================
echo.

REM ---------------------------------------------------------------- 1. python
set "PY="
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%ProgramFiles%\Python311\python.exe"
    "%ProgramFiles%\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python312\python.exe"
) do (
    if not defined PY if exist %%P set "PY=%%~P"
)
if not defined PY (
    echo [ERROR] Official Python 3.11/3.12 not found.
    echo         Download and install - click Install Now, do NOT tick Add to PATH:
    echo         https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
    echo         Then run this script again.
    pause
    exit /b 1
)
"%PY%" -c "import sys;sys.exit(1 if 'conda' in sys.version.lower() else 0)" || (
    echo [ERROR] %PY% is a conda build - refusing. Install python.org Python.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('"%PY%" -c "import sys;print(sys.version.split()[0])"') do echo [*] Using official Python %%v  at  %PY%

REM ---------------------------------------------------------------- 2. venv
set "VENV=%~dp0.venv_official"
if exist "%VENV%\Scripts\python.exe" (
    echo [*] Reusing existing %VENV%
) else (
    echo [*] Creating virtual environment %VENV% ...
    "%PY%" -m venv "%VENV%" || (echo [ERROR] venv creation failed & pause & exit /b 1)
)
call "%VENV%\Scripts\activate.bat"
set CONDA_PREFIX=
set CONDA_DEFAULT_ENV=
set PYTHONHOME=
set PYTHONPATH=
set "PATH=%VENV%\Scripts;%SystemRoot%\System32;%SystemRoot%;%SystemRoot%\System32\WindowsPowerShell\v1.0"
python -c "import sys;print('[*] venv python:',sys.version.split()[0],'base:',sys.base_prefix)"

REM ---------------------------------------------------------------- 3. deps
set "MIRROR=https://mirror-pypi.runflare.com/simple"
set "MHOST=mirror-pypi.runflare.com"
python -m pip install --disable-pip-version-check -q -U pip || python -m pip install -q -U pip -i %MIRROR% --trusted-host %MHOST%
call :PIPI "PySide6==6.8.3"
call :PIPI "numpy<2.3"
call :PIPI brotli pillow python-dotenv orjson httpx openai pytesseract pymupdf
call :PIPI "nuitka>=2.4" zstandard
call :PIPI ordered-set
echo [*] Verifying imports ...
python -c "import PySide6.QtCore, brotli, numpy, PIL, dotenv, orjson, httpx, openai, nuitka; print('[*] all core imports OK')" || (
    echo [ERROR] A core package failed to import - see message above.
    pause
    exit /b 1
)

REM ---------------------------------------------------------------- 4. preflight
python "%~dp0preflight_check.py" || (
    echo [ERROR] Pre-flight failed - fix the listed problems and re-run.
    pause
    exit /b 1
)

REM ---------------------------------------------------------------- 5. build
REM build_nuitka.bat activates .venv if present; we hand it the official one instead.
if exist "%~dp0.venv" if not exist "%~dp0.venv_conda_backup" (
    echo [*] Parking the old conda venv as .venv_conda_backup  - not deleted
    ren "%~dp0.venv" ".venv_conda_backup"
)
if not exist "%~dp0.venv" mklink /J "%~dp0.venv" "%VENV%" >nul 2>&1
if not exist "%~dp0.venv" (
    echo [ERROR] Could not link .venv to .venv_official. Run as administrator or rename manually:
    echo         ren .venv_official .venv
    pause
    exit /b 1
)
if not defined HEMOGLYPH_JOBS set HEMOGLYPH_JOBS=2
set HEMOGLYPH_NOPAUSE=1
echo [*] Starting Nuitka build - LITE mode, %HEMOGLYPH_JOBS% jobs. This takes 20-60 minutes.
call "%~dp0build_nuitka.bat" lite
if errorlevel 1 (
    echo [ERROR] Build failed - see above.
    pause
    exit /b 1
)

REM ---------------------------------------------------------------- 6. smoke test
echo.
echo [*] Smoke test: launching dist\app.dist\Hemoglyph.exe for 12 seconds ...
pushd "%~dp0dist\app.dist"
start "" Hemoglyph.exe
timeout /t 12 >nul
tasklist | findstr /i "Hemoglyph.exe" >nul
if errorlevel 1 (
    echo [WARN] Hemoglyph.exe is not running after 12 s. Capturing startup output ...
    Hemoglyph.exe > run.txt 2>&1
    timeout /t 8 >nul
    echo ---------------- run.txt ----------------
    type run.txt
    echo -----------------------------------------
    if exist hemoglyph_startup_error.log type hemoglyph_startup_error.log
    if exist qml_load_error.log type qml_load_error.log
    popd
    pause
    exit /b 1
)
echo [OK] Hemoglyph.exe is running. Closing it and creating the desktop shortcut ...
taskkill /f /im Hemoglyph.exe >nul 2>&1
call Create_Desktop_Shortcut.bat
popd
echo.
echo ======================================================================
echo   DONE.  dist\app.dist\Hemoglyph.exe  +  desktop shortcut "Hemoglyph CDSS"
echo ======================================================================
pause
exit /b 0

:PIPI
python -m pip install --disable-pip-version-check -q %* && exit /b 0
echo [*] PyPI failed for %* - trying Iranian mirror ...
python -m pip install --disable-pip-version-check -q -i %MIRROR% --trusted-host %MHOST% %* && exit /b 0
echo [WARN] could not install %*
exit /b 0
