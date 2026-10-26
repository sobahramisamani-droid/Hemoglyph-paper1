@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title HEMOGLYPH All-in-One Master Builder
color 0b

echo ======================================================================
echo   HEMOGLYPH ALL-IN-ONE AUTOMATED MASTER BUILDER (v1.3.1)
echo   Compile + Ingest DLLs + Clean 'bin' Structure + Desktop Shortcut + ZIP
echo ======================================================================
echo.

REM 1. Unconditionally Activate Virtual Environment
if exist "%~dp0.venv\Scripts\activate.bat" (
    call "%~dp0.venv\Scripts\activate.bat"
) else if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

REM 2. Sanitize Environment (Eliminate Anaconda DLL pollution)
set CONDA_PREFIX=
set CONDA_DEFAULT_ENV=
set PYTHONHOME=
if exist "%~dp0.venv\Scripts" (
    set "PATH=%~dp0.venv\Scripts;%~dp0.venv\Lib\site-packages\PySide6;%~dp0.venv\Lib\site-packages\PySide6\Qt\bin;C:\Windows\System32;C:\Windows"
)

REM 3. Verify Python Runtime
set PYTHON_CMD=python
if exist "%~dp0.venv\Scripts\python.exe" set "PYTHON_CMD=%~dp0.venv\Scripts\python.exe"

echo [*] Using Python: %PYTHON_CMD%
%PYTHON_CMD% -c "import sys; print(f'[*] Python Runtime: {sys.version.split()[0]} (64-bit)')" 2>nul
%PYTHON_CMD% -c "import PySide6.QtCore; print('[*] PySide6 QtCore verified successfully.')" 2>nul

REM 4. Ensure Compiler and Packaging Tools
echo [*] Ensuring build prerequisites (Nuitka, Brotli, OpenAI, HTTPX)...
%PYTHON_CMD% -m pip install nuitka zstandard brotli openai httpx >nul 2>&1

REM 5. Pre-compress Registries with Brotli if needed
if exist "%~dp0br.py" (
    %PYTHON_CMD% "%~dp0br.py"
)

REM 6. Multi-Core Turbo Speed Tuning
set CPU_CORES=%NUMBER_OF_PROCESSORS%
if not defined CPU_CORES set CPU_CORES=8
echo [*] Turbo Multi-Threading: Active on all %CPU_CORES% CPU cores!

REM 7. Gather Clinical Data Registries and Icons
set DATA_FLAGS=
if exist HEMOGLYPH_FEATURE_REGISTRY.json.br set DATA_FLAGS=!DATA_FLAGS! --include-data-files=HEMOGLYPH_FEATURE_REGISTRY.json.br=HEMOGLYPH_FEATURE_REGISTRY.json.br
if exist HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br set DATA_FLAGS=!DATA_FLAGS! --include-data-files=HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br=HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br
if exist HEMOGLYPH_GUIDELINE_REGISTRY.json.br set DATA_FLAGS=!DATA_FLAGS! --include-data-files=HEMOGLYPH_GUIDELINE_REGISTRY.json.br=HEMOGLYPH_GUIDELINE_REGISTRY.json.br
if exist app_icon.png set DATA_FLAGS=!DATA_FLAGS! --include-data-files=app_icon.png=app_icon.png
if exist app_icon.ico set DATA_FLAGS=!DATA_FLAGS! --include-data-files=app_icon.ico=app_icon.ico
if exist .env.example set DATA_FLAGS=!DATA_FLAGS! --include-data-files=.env.example=.env.example
if exist models set DATA_FLAGS=!DATA_FLAGS! --include-data-dir=models=models

set ICON_FLAG=
if exist app_icon.ico set ICON_FLAG=--windows-icon-from-ico=app_icon.ico
if not defined ICON_FLAG if exist icon.ico set ICON_FLAG=--windows-icon-from-ico=icon.ico

echo.
echo ======================================================================
echo   [STEP 1/3] TURBO C++ COMPILATION (PROPRIETARY CLINICAL LOGIC ONLY)
echo   * External libraries are harvested instantly via Post-Build
echo   * Compiling 14 proprietary CDSS modules at maximum CPU velocity
echo ======================================================================
echo.

%PYTHON_CMD% -m nuitka ^
    --standalone ^
    --enable-plugin=pyside6 ^
    --include-qt-plugins=sensible,qml ^
    --include-data-dir=qml=qml ^
    --include-package=brotli ^
    --include-module=license_engine ^
    --include-module=sarvis_tahlil ^
    --include-module=calcu ^
    --include-module=paygah_dade ^
    --include-module=naam_haye_vizhegi ^
    --include-module=models_scientific_references ^
    --include-module=namaye_registry ^
    --include-module=analyse_gidlines ^
    --include-module=prdicter ^
    --include-module=AI ^
    --include-module=ocr ^
    --include-module=ocr_consistency ^
    --include-module=ocr_confidence ^
    --include-module=_ocr_support ^
    --include-module=cache_registry ^
    --assume-yes-for-downloads ^
    --nofollow-import-to=pymupdf ^
    --nofollow-import-to=fitz ^
    --nofollow-import-to=cv2 ^
    --nofollow-import-to=paddleocr ^
    --nofollow-import-to=paddle ^
    --nofollow-import-to=sklearn ^
    --nofollow-import-to=onnxruntime ^
    --nofollow-import-to=requests ^
    --nofollow-import-to=urllib3 ^
    --nofollow-import-to=pkg_resources ^
    --nofollow-import-to=PIL.ImageTk ^
    --nofollow-import-to=torch ^
    --nofollow-import-to=scipy ^
    --nofollow-import-to=matplotlib ^
    --nofollow-import-to=pandas ^
    --nofollow-import-to=IPython ^
    --nofollow-import-to=notebook ^
    --nofollow-import-to=fontTools ^
    --nofollow-import-to=aiohttp ^
    --nofollow-import-to=chardet ^
    --nofollow-import-to=unittest ^
    --nofollow-import-to=pytest ^
    --nofollow-import-to=distutils ^
    --nofollow-import-to=setuptools ^
    --nofollow-import-to=pip ^
    --nofollow-import-to=tkinter ^
    --lto=no ^
    --low-memory ^
    --jobs=%CPU_CORES% ^
    --windows-console-mode=disable ^
    --company-name="Hemoglyph Medical CDSS" ^
    --product-name="Hemoglyph Clinical Decision Support Suite" ^
    --file-version=1.3.1.0 ^
    --product-version=1.3.1 ^
    --file-description="Hemoglyph Clinical Decision Support Suite (RSA-4096 Protected)" ^
    --copyright="Copyright (C) 2026 Sobhan Bahrami. All rights reserved." ^
    !ICON_FLAG! ^
    !DATA_FLAGS! ^
    --output-filename=Hemoglyph.exe ^
    --output-dir=dist ^
    app.py

if errorlevel 1 (
    echo.
    echo [ERROR] Nuitka compilation failed. Please check messages above.
    pause
    exit /b 1
)

echo.
echo ======================================================================
echo   [STEP 2/3] SURGICAL POST-BUILD HARVESTER (INGESTING ESSENTIAL DLLs)
echo ======================================================================
echo.
%PYTHON_CMD% "%~dp0_post_build.py"

echo.
echo ======================================================================
echo   [STEP 3/3] ORGANIZING CLEAN 'bin' STRUCTURE & DESKTOP SHORTCUT CREATOR
echo ======================================================================
echo.
%PYTHON_CMD% "%~dp0_organize_release.py"

echo.
echo ======================================================================
echo   [ALL DONE - 100%% SUCCESS]
echo   1. All DLLs and PySide6 folders organized into 'bin\'
echo   2. Desktop Shortcut Builder (Create_Desktop_Shortcut.bat) placed in root
echo   3. Silent launcher (Hemoglyph.vbs) ready
echo   4. Clean ZIP package created in dist\ folder!
echo ======================================================================
echo.
pause
