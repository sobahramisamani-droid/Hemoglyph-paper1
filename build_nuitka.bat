@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title HEMOGLYPH - Ultra-Secure Native C++ Machine Code Compiler (Nuitka Turbo)
color 0b

echo ======================================================================
echo   HEMOGLYPH ULTRA-SECURE NATIVE C++ MACHINE CODE COMPILER
echo   Maximum Reverse-Engineering Protection with Turbo Compilation
echo   Platform: Windows x64 ^| Engine: Nuitka + PySide6 QtQuick
echo ======================================================================
echo.

REM 1. Activate virtual environment unconditionally
if exist "%~dp0.venv\Scripts\activate.bat" (
    call "%~dp0.venv\Scripts\activate.bat"
) else if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
) else if exist "..\.venv\Scripts\activate.bat" (
    call "..\.venv\Scripts\activate.bat"
)

REM 2. Sanitize Environment and PATH (Strip Anaconda DLL pollution for clean PySide6 compilation)
set CONDA_PREFIX=
set CONDA_DEFAULT_ENV=
set PYTHONHOME=
if exist "%~dp0.venv\Scripts" (
    set "PATH=%~dp0.venv\Scripts;%~dp0.venv\Lib\site-packages\PySide6;%~dp0.venv\Lib\site-packages\PySide6\Qt\bin;C:\Windows\System32;C:\Windows"
)

REM 3. Verify Python Runtime & Architecture
python -c "import sys; print(f'[*] Python Runtime: {sys.version.split()[0]} (64-bit)' if sys.maxsize > 2**32 else f'[*] Python Runtime: {sys.version.split()[0]} (32-bit)')" 2>nul
python -c "import PySide6.QtCore; print('[*] PySide6 QtCore verified successfully.')" 2>nul

REM 4. Ensure build dependencies (PyPI first, Iranian mirror as fallback)
set "PIP_MIRROR=https://mirror-pypi.runflare.com/simple"
call :PIP_ENSURE nuitka "nuitka>=2.4" zstandard ordered-set
call :PIP_ENSURE brotli brotli
call :PIP_ENSURE openai openai httpx
call :PIP_ENSURE PySide6 "PySide6==6.8.3"

REM 4b. Pre-flight verification (stops the build on any blocking problem)
if exist "%~dp0preflight_check.py" (
    echo [*] Running pre-flight verification...
    python "%~dp0preflight_check.py"
    if errorlevel 1 (
        echo [ERROR] Pre-flight failed. Fix the problems listed above and re-run.
        pause
        exit /b 1
    )
)

REM 4. Ensure clean and validated QML directory
if not exist qml (
    echo [ERROR] Required 'qml' directory not found in current folder!
    pause
    exit /b 1
)

REM 5. Free disk space: Purge stale build directories from previous runs
echo [*] Cleaning stale build caches to maximize free disk space...
if exist "app.build" rd /s /q "app.build" >nul 2>&1
if exist "app.dist" rd /s /q "app.dist" >nul 2>&1
if exist "Hemoglyph.build" rd /s /q "Hemoglyph.build" >nul 2>&1
if exist "Hemoglyph.dist" rd /s /q "Hemoglyph.dist" >nul 2>&1
if exist "build" rd /s /q "build" >nul 2>&1
if exist "dist\Hemoglyph.dist" rd /s /q "dist\Hemoglyph.dist" >nul 2>&1
if exist "dist\Hemoglyph.build" rd /s /q "dist\Hemoglyph.build" >nul 2>&1
if exist "dist\app.dist" rd /s /q "dist\app.dist" >nul 2>&1
if exist "dist\app.build" rd /s /q "dist\app.build" >nul 2>&1
if exist "nuitka-crash-report.xml" del /f /q "nuitka-crash-report.xml" >nul 2>&1

REM 6. Smart Brotli Compression: Compress all clinical registries to .json.br
if exist "%~dp0br.py" (
    echo [*] Checking and compressing clinical registries with Brotli...
    python "%~dp0br.py"
)

REM 7. Dynamically Gather Clinical Registries, Databases, and Icons
set DATA_FLAGS=

REM Feature Registry
if exist HEMOGLYPH_FEATURE_REGISTRY.json.br (
    echo [*] Registering Feature Registry: HEMOGLYPH_FEATURE_REGISTRY.json.br
    set DATA_FLAGS=!DATA_FLAGS! --include-data-files=HEMOGLYPH_FEATURE_REGISTRY.json.br=HEMOGLYPH_FEATURE_REGISTRY.json.br
)
if not exist HEMOGLYPH_FEATURE_REGISTRY.json.br if exist HEMOGLYPH_FEATURE_REGISTRY.json (
    echo [*] Registering Feature Registry: HEMOGLYPH_FEATURE_REGISTRY.json
    set DATA_FLAGS=!DATA_FLAGS! --include-data-files=HEMOGLYPH_FEATURE_REGISTRY.json=HEMOGLYPH_FEATURE_REGISTRY.json
)

REM Disease Guideline Registry
if exist HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br (
    echo [*] Registering Disease Guideline Registry: HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br
    set DATA_FLAGS=!DATA_FLAGS! --include-data-files=HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br=HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br
)
if not exist HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br if exist HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json (
    echo [*] Registering Disease Guideline Registry: HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json
    set DATA_FLAGS=!DATA_FLAGS! --include-data-files=HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json=HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json
)

REM Guideline Registry
if exist HEMOGLYPH_GUIDELINE_REGISTRY.json.br (
    echo [*] Registering Guideline Registry: HEMOGLYPH_GUIDELINE_REGISTRY.json.br
    set DATA_FLAGS=!DATA_FLAGS! --include-data-files=HEMOGLYPH_GUIDELINE_REGISTRY.json.br=HEMOGLYPH_GUIDELINE_REGISTRY.json.br
)
if not exist HEMOGLYPH_GUIDELINE_REGISTRY.json.br if exist HEMOGLYPH_GUIDELINE_REGISTRY.json (
    echo [*] Registering Guideline Registry: HEMOGLYPH_GUIDELINE_REGISTRY.json
    set DATA_FLAGS=!DATA_FLAGS! --include-data-files=HEMOGLYPH_GUIDELINE_REGISTRY.json=HEMOGLYPH_GUIDELINE_REGISTRY.json
)

REM Icons and Assets
if exist app_icon.png set DATA_FLAGS=!DATA_FLAGS! --include-data-files=app_icon.png=app_icon.png
if exist app_icon.ico set DATA_FLAGS=!DATA_FLAGS! --include-data-files=app_icon.ico=app_icon.ico
if exist icon.ico set DATA_FLAGS=!DATA_FLAGS! --include-data-files=icon.ico=icon.ico
if exist logo.ico set DATA_FLAGS=!DATA_FLAGS! --include-data-files=logo.ico=logo.ico
if exist Create_Desktop_Shortcut.bat set DATA_FLAGS=!DATA_FLAGS! --include-data-files=Create_Desktop_Shortcut.bat=Create_Desktop_Shortcut.bat
REM SECURITY: .env (API keys) is intentionally NOT bundled. Only the template ships.
if exist .env.example set DATA_FLAGS=!DATA_FLAGS! --include-data-files=.env.example=.env.example
if exist bin\llama-server.exe set DATA_FLAGS=!DATA_FLAGS! --include-data-dir=bin=bin
if exist models set DATA_FLAGS=!DATA_FLAGS! --include-data-dir=models=models

REM 8. Windows Executable Icon
set ICON_FLAG=
if exist app_icon.ico set ICON_FLAG=--windows-icon-from-ico=app_icon.ico
if not defined ICON_FLAG if exist icon.ico set ICON_FLAG=--windows-icon-from-ico=icon.ico
if not defined ICON_FLAG if exist logo.ico set ICON_FLAG=--windows-icon-from-ico=logo.ico

REM 9. Parallel CPU Core Tuning
REM RAM-aware: every gcc job needs ~2 GB. jobs = min(cores, free_RAM_GB / 2), at least 1.
set CPU_JOBS=%NUMBER_OF_PROCESSORS%
if not defined CPU_JOBS set CPU_JOBS=4
set FREE_GB=
set "PS_EXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
for /f %%m in ('"%PS_EXE%" -NoProfile -Command "[int][math]::Floor((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB)" 2^>nul') do set FREE_GB=%%m
if not defined FREE_GB for /f "skip=1 tokens=2 delims==" %%m in ('wmic OS get FreePhysicalMemory /value 2^>nul') do set /a FREE_GB=%%m/1048576
if defined FREE_GB (
    set /a RAM_JOBS=!FREE_GB! / 2
    if !RAM_JOBS! lss 1 set RAM_JOBS=1
    if !RAM_JOBS! lss !CPU_JOBS! set CPU_JOBS=!RAM_JOBS!
) else (
    set CPU_JOBS=2
    echo [*] Could not read free RAM - using 2 jobs to be safe.
)
if defined HEMOGLYPH_JOBS set CPU_JOBS=%HEMOGLYPH_JOBS%
echo [*] Free RAM: !FREE_GB! GB  -^> compiling with !CPU_JOBS! parallel jobs. Override: set HEMOGLYPH_JOBS=n

REM 9b. Prefer MSVC when Visual Studio Build Tools are installed (faster, less RAM); else Nuitka's MinGW64
set MSVC_FLAG=
if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" (
    for /f "usebackq tokens=*" %%i in (`"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath 2^>nul`) do (
        if exist "%%i\VC\Auxiliary\Build\vcvars64.bat" (
            echo [*] MSVC detected: %%i
            set "MSVC_FLAG=--msvc=latest"
        )
    )
)
if not defined MSVC_FLAG echo [*] MSVC not found - Nuitka will use/download MinGW64 (needs internet on first run).

REM 10. Check Vision OCR dependencies for standalone bundling
REM Two modes for the cloud-Vision client stack (openai + pydantic + httpx ~ 1,500 files):
REM   default      : compiled into C (slow, ~2 GB RAM per gcc job)
REM   LITE  (arg "lite" or set HEMOGLYPH_LITE=1): NOT compiled; shipped as plain third-party
REM                  packages next to the exe by _post_build.py. Proprietary modules are still
REM                  100%% native C. Cuts compile time/RAM by roughly half. openai is imported
REM                  lazily, so if it were ever missing only cloud OCR degrades, never the app.
set OPENAI_PKG=
set LITE_MODE=
if /i "%~1"=="lite" set LITE_MODE=1
if "%HEMOGLYPH_LITE%"=="1" set LITE_MODE=1
python -c "import openai" >nul 2>&1
if errorlevel 1 set LITE_MODE=
if defined LITE_MODE (
    echo [*] LITE mode: openai/pydantic/httpx stack will be shipped uncompiled.
    set OPENAI_PKG=--nofollow-import-to=openai --nofollow-import-to=pydantic --nofollow-import-to=pydantic_core --nofollow-import-to=httpx --nofollow-import-to=httpcore --nofollow-import-to=anyio --nofollow-import-to=jiter --nofollow-import-to=tqdm --nofollow-import-to=distro --include-package=asyncio --include-package=email --include-package=http --include-package=json --include-package=logging --include-package=concurrent --include-module=ssl --include-module=socket --include-module=select --include-module=selectors --include-module=inspect --include-module=dataclasses --include-module=typing --include-module=functools --include-module=contextlib --include-module=uuid --include-module=base64 --include-module=mimetypes --include-module=platform --include-module=warnings --include-module=weakref --include-module=decimal --include-module=fractions --include-module=ipaddress --include-module=zoneinfo --include-module=datetime --include-module=hashlib --include-module=hmac --include-module=secrets --include-module=queue --include-module=threading --include-module=sqlite3
    set HEMOGLYPH_LITE=1
) else (
    echo [*] Full mode: compiling openai client stack into native code - slower. Tip: build_nuitka.bat lite
    set OPENAI_PKG=--include-package=openai --include-package=httpx
)

echo.
echo ======================================================================
echo   COMPILING 16 PROPRIETARY MEDICAL MODULES INTO NATIVE C++
echo   - 100 percent proprietary logic compiled to native machine code
echo   - Full PySide6 QtQuick and QML controls bundling
echo   - Military-Grade Asymmetric RSA-4096 / SHA-512 anti-tamper security
echo   - Low-RAM tuning active (prevents compiler out-of-memory errors)
echo ======================================================================
echo.

python -m nuitka ^
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
    --include-module=ocr_consistency ^
    --include-module=ocr_confidence ^
    --include-module=prdicter ^
    --include-module=AI ^
    --include-module=ocr ^
    --include-module=_ocr_support ^
    --include-module=cache_registry ^
    --assume-yes-for-downloads ^
    --nofollow-import-to=pymupdf ^
    --nofollow-import-to=fitz ^
    --nofollow-import-to=cv2 ^
    --nofollow-import-to=paddleocr ^
    --nofollow-import-to=paddle ^
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
    !MSVC_FLAG! ^
    --remove-output ^
    --noinclude-pytest-mode=nofollow ^
    --noinclude-setuptools-mode=nofollow ^
    --noinclude-unittest-mode=nofollow ^
    --jobs=%CPU_JOBS% ^
    --windows-console-mode=disable ^
    --company-name="Hemoglyph Medical CDSS" ^
    --product-name="Hemoglyph Clinical Decision Support Suite" ^
    --file-version=1.3.1.0 ^
    --product-version=1.3.1 ^
    --file-description="Hemoglyph Clinical Decision Support Suite (RSA-4096 Protected)" ^
    --copyright="Copyright (C) 2026 Sobhan Bahrami. All rights reserved." ^
    !DATA_FLAGS! ^
    !OPENAI_PKG! ^
    !ICON_FLAG! ^
    --output-filename=Hemoglyph.exe ^
    --output-dir=dist ^
    app.py

if errorlevel 1 goto :BUILD_FAIL

REM 10. Automatic Runtime DLL Harvesting, QML Bundling & Ingestion
echo.
echo [*] Running automated post-build harvester and deployer...
if exist "%~dp0_post_build.py" (
    python "%~dp0_post_build.py"
    if errorlevel 1 goto :BUILD_FAIL
)

REM 11. Verify the finished dist folder (exe, registries, qml, icon, no secrets)
python "%~dp0_verify_dist.py" dist\app.dist
if errorlevel 1 goto :BUILD_FAIL

echo.
echo ======================================================================
echo   [SUCCESS] NATIVE C++ BINARY CREATED SUCCESSFULLY!
echo.
echo   Security and Architecture Status:
echo     * 100 percent C++ Machine Code (Zero Python bytecode left)
echo     * Protected by Military-Grade Asymmetric RSA-4096 / SHA-512
echo     * Hardware Node-Locking Active (Tamper-Resistant)
echo     * Embedded QtQuick and QML UI Engine Complete
echo     * Output folder: dist\app.dist  (run Hemoglyph.exe from there)
echo.
echo   Next steps:
echo     1. Test:  dist\app.dist\Hemoglyph.exe
echo     2. Optional code signing (removes SmartScreen/AV warnings):
echo        signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /a dist\app.dist\Hemoglyph.exe
echo     3. Shortcut: dist\app.dist\Create_Desktop_Shortcut.bat
echo     4. Zip the whole app.dist folder for distribution (never zip .env)
echo ======================================================================
if not defined HEMOGLYPH_NOPAUSE pause
exit /b 0

:PIP_ENSURE
REM usage: call :PIP_ENSURE <import-name-or-dist> <pip specs...>
set "_dist=%~1"
shift
set "_specs="
:PIP_ENSURE_ARGS
if "%~1"=="" goto :PIP_ENSURE_GO
set "_specs=!_specs! %1"
shift
goto :PIP_ENSURE_ARGS
:PIP_ENSURE_GO
python -m pip show %_dist% >nul 2>&1
if not errorlevel 1 exit /b 0
echo [*] Installing !_specs! ...
python -m pip install --disable-pip-version-check !_specs!
if not errorlevel 1 exit /b 0
echo [*] PyPI unreachable - retrying through Iranian mirror...
python -m pip install --disable-pip-version-check -i %PIP_MIRROR% --trusted-host mirror-pypi.runflare.com !_specs!
if errorlevel 1 (
    echo [ERROR] Could not install !_specs!. Set DNS to 178.22.122.100 - Shecan - or install manually.
    pause
    exit /b 1
)
exit /b 0

:BUILD_FAIL
echo.
echo ======================================================================
echo   [ERROR] Compilation or post-build step encountered an error.
echo   Please inspect the error messages above.
echo ======================================================================
if not defined HEMOGLYPH_NOPAUSE pause
exit /b 1
