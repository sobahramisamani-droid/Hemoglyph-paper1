@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Hemoglyph - dependency check
REM ---------------------------------------------------------------------
REM  Checks every third-party package Hemoglyph imports; installs what is
REM  missing (PyPI first, Iranian mirror as fallback). Safe to run any time.
REM  Usage:  ensure_deps.bat          (inside the activated .venv)
REM ---------------------------------------------------------------------
if exist "%~dp0.venv\Scripts\activate.bat" call "%~dp0.venv\Scripts\activate.bat"
set CONDA_PREFIX=
set PYTHONHOME=
set "MIRROR=https://mirror-pypi.runflare.com/simple"
set "MIRROR_HOST=mirror-pypi.runflare.com"

python -c "import sys" >nul 2>&1 || (echo [ERROR] python not found - activate the venv first & pause & exit /b 1)
for /f "tokens=*" %%v in ('python -c "import sys;print(sys.version.split()[0])"') do echo [*] Python %%v

REM  format:  import_name=pip_spec     (REQUIRED = app will not start without it)
set N=0
call :ADD PySide6      "PySide6==6.8.3"        REQUIRED
call :ADD brotli       brotli                  REQUIRED
call :ADD numpy        "numpy<2.3"             REQUIRED
call :ADD PIL          pillow                  REQUIRED
call :ADD dotenv       python-dotenv           REQUIRED
call :ADD orjson       orjson                  REQUIRED
call :ADD httpx        httpx                   REQUIRED
call :ADD openai       openai                  REQUIRED
call :ADD pytesseract  pytesseract             OPTIONAL
call :ADD fitz         pymupdf                 OPTIONAL
call :ADD cv2          opencv-python-headless  OPTIONAL
call :ADD nuitka       "nuitka>=2.4"           BUILD
call :ADD zstandard    zstandard               BUILD
call :ADD ordered_set  ordered-set             BUILD
call :ADD pytest       pytest                  BUILD

set MISSING=
set FAILED=
for /l %%i in (1,1,%N%) do (
    python -c "import !IMP[%%i]!" >nul 2>&1
    if errorlevel 1 (
        echo [MISSING] !IMP[%%i]!  ^(!KIND[%%i]!^)  -^> installing !SPEC[%%i]!
        call :INSTALL !SPEC[%%i]!
        if errorlevel 1 (
            set "FAILED=!FAILED! !SPEC[%%i]!"
        ) else (
            python -c "import !IMP[%%i]!" >nul 2>&1 && echo [OK]      !IMP[%%i]! installed || set "FAILED=!FAILED! !SPEC[%%i]!"
        )
    ) else (
        echo [OK]      !IMP[%%i]!
    )
)

echo.
if defined FAILED (
    echo [WARN] Could not install:%FAILED%
    echo        Fix DNS ^(Shecan 178.22.122.100^) or install manually, then re-run.
) else (
    echo [SUCCESS] All packages present.
)
echo.
echo [*] Tesseract OCR engine ^(not a pip package^):
where tesseract >nul 2>&1 && (tesseract --version 2>nul | findstr /i "tesseract") || echo     not on PATH - optional; install Tesseract 5 from https://github.com/UB-Mannheim/tesseract/wiki if you want local OCR
pause
exit /b 0

:ADD
set /a N+=1
set "IMP[%N%]=%~1"
set "SPEC[%N%]=%~2"
set "KIND[%N%]=%~3"
exit /b 0

:INSTALL
python -m pip install --disable-pip-version-check -q %* && exit /b 0
echo           PyPI failed - trying Iranian mirror...
python -m pip install --disable-pip-version-check -q -i %MIRROR% --trusted-host %MIRROR_HOST% %* && exit /b 0
exit /b 1
