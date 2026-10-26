@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title HEMOGLYPH - download official Python 3.11 + build venv
color 0b
echo ======================================================================
echo   HEMOGLYPH  -  self-contained toolchain
echo   downloads official python.org Python 3.11.9 (64-bit) into
echo       %~dp0.python311
echo   creates  .venv  from it and installs the pinned packages.
echo   Nothing system-wide is touched. Anaconda is never used.
echo ======================================================================
echo.

set "PYVER=3.11.9"
set "PYDIR=%~dp0.python311"
set "PYEXE=%PYDIR%\python.exe"
set "INST=%TEMP%\python-%PYVER%-amd64.exe"
set "VENV=%~dp0.venv"

REM ------------------------------------------------ 1. download installer
if exist "%PYEXE%" (
    echo [*] Python already present: %PYEXE%
    goto :MAKE_VENV
)
set "URLS=https://www.python.org/ftp/python/%PYVER%/python-%PYVER%-amd64.exe https://mirrors.huaweicloud.com/python/%PYVER%/python-%PYVER%-amd64.exe https://registry.npmmirror.com/-/binary/python/%PYVER%/python-%PYVER%-amd64.exe"
if exist "%INST%" del /f /q "%INST%"
for %%U in (%URLS%) do (
    if not exist "%INST%" (
        echo [*] Downloading %%U
        curl.exe -L --fail --retry 2 --connect-timeout 20 -o "%INST%" "%%U" 2>nul
        if not exist "%INST%" powershell -NoProfile -Command "try{[Net.ServicePointManager]::SecurityProtocol='Tls12';Invoke-WebRequest -Uri '%%U' -OutFile '%INST%' -UseBasicParsing}catch{}"
    )
)
if not exist "%INST%" (
    echo [ERROR] Could not download Python from any mirror. Download manually:
    echo         https://www.python.org/ftp/python/%PYVER%/python-%PYVER%-amd64.exe
    echo         save it as  %INST%  and run this script again.
    pause
    exit /b 1
)
for %%S in ("%INST%") do set SIZE=%%~zS
if %SIZE% LSS 20000000 (
    echo [ERROR] Downloaded file is too small ^(%SIZE% bytes^) - blocked or corrupted. Delete it and retry.
    pause
    exit /b 1
)

REM ------------------------------------------------ 2. silent, local, per-user install
echo [*] Installing Python %PYVER% into %PYDIR%  ...
"%INST%" /quiet InstallAllUsers=0 TargetDir="%PYDIR%" PrependPath=0 AssociateFiles=0 Shortcuts=0 Include_launcher=0 Include_test=0 Include_doc=0 InstallLauncherAllUsers=0 SimpleInstall=1
if not exist "%PYEXE%" (
    echo [ERROR] Installation failed. Run the installer manually: %INST%
    echo         choose Customize - Install for me only - location %PYDIR%
    pause
    exit /b 1
)
"%PYEXE%" -c "import sys,struct;print('[*] Installed:',sys.version.split()[0],struct.calcsize('P')*8,'bit')"

:MAKE_VENV
REM ------------------------------------------------ 3. venv
if exist "%VENV%\Scripts\python.exe" (
    echo [*] .venv exists - removing it to rebuild cleanly ^(you asked for a from-scratch venv^)
    rd /s /q "%VENV%"
)
"%PYEXE%" -m venv "%VENV%" || (echo [ERROR] venv creation failed & pause & exit /b 1)
call "%VENV%\Scripts\activate.bat"
set CONDA_PREFIX=
set PYTHONHOME=
set PYTHONPATH=
python -c "import sys;print('[*] venv python:',sys.version.split()[0],'| base:',sys.base_prefix)"

REM ------------------------------------------------ 4. pinned packages
set "MIRROR=https://mirror-pypi.runflare.com/simple"
set "MHOST=mirror-pypi.runflare.com"
call :PIPI pip==24.3.1 setuptools==75.8.0 wheel==0.45.1
call :PIPI PySide6==6.8.3
call :PIPI numpy==2.2.6 pillow==11.1.0 brotli==1.1.0 orjson==3.10.15 python-dotenv==1.0.1
call :PIPI httpx==0.28.1 openai==1.66.3
call :PIPI pytesseract==0.3.13 pymupdf==1.25.3
call :PIPI nuitka==2.6.9 zstandard==0.23.0 ordered-set==4.1.0
call :PIPI pytest==8.3.5

echo.
echo [*] Verifying imports ...
python -c "import PySide6.QtCore, brotli, numpy, PIL, dotenv, orjson, httpx, openai, nuitka, pytesseract, fitz; print('[OK] all imports fine')" || (
    echo [ERROR] An import failed - see above. Re-run the matching pip line manually.
    pause
    exit /b 1
)
echo.
if exist "%~dp0preflight_check.py" python "%~dp0preflight_check.py"
echo.
echo ======================================================================
echo   READY.  Next:
echo      .venv\Scripts\activate
echo      set HEMOGLYPH_JOBS=2
echo      build_nuitka.bat lite
echo ======================================================================
pause
exit /b 0

:PIPI
echo [*] pip install %*
python -m pip install --disable-pip-version-check -q %* && exit /b 0
echo     PyPI failed - trying Iranian mirror ...
python -m pip install --disable-pip-version-check -q -i %MIRROR% --trusted-host %MHOST% %* && exit /b 0
echo [WARN] could not install: %*
exit /b 0
