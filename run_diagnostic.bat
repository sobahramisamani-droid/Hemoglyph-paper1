@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Hemoglyph Diagnostic and Console Debugger
color 0e

echo ======================================================================
echo   HEMOGLYPH STARTUP DIAGNOSTIC AND CONSOLE DEBUGGER
echo ======================================================================
echo.

REM 1. Activate venv if present
if exist ..\.venv\Scripts\activate.bat (
    call ..\.venv\Scripts\activate.bat
) else if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

REM 2. Run post-build harvester if present
if exist "%~dp0_post_build.py" (
    echo [*] Checking runtime dependencies...
    python "%~dp0_post_build.py" >nul 2>&1
)

REM 3. Comprehensive multi-location search for Hemoglyph.exe
set TARGET_EXE=
set TARGET_DIR=

for %%P in (
    "Hemoglyph.exe"
    "bin\Hemoglyph.exe"
    "dist\HEMOGLYPH_ALA_1.3.1\bin\Hemoglyph.exe"
    "dist\HEMOGLYPH_ALA_1.3.1\Hemoglyph.exe"
    "dist\app.dist\Hemoglyph.exe"
    "dist\Hemoglyph.dist\Hemoglyph.exe"
    "app.dist\Hemoglyph.exe"
    "Hemoglyph.dist\Hemoglyph.exe"
    "..\Hemoglyph.exe"
    "..\bin\Hemoglyph.exe"
) do (
    if not defined TARGET_EXE (
        if exist "%%~fP" (
            set "TARGET_EXE=%%~fP"
            set "TARGET_DIR=%%~dpP"
        )
    )
)

if defined TARGET_EXE (
    echo [*] Target executable identified: !TARGET_EXE!
    echo [*] Working directory: !TARGET_DIR!
    echo.

    REM Patch Hemoglyph.exe to Console mode temporarily so stdout/stderr prints in CMD
    echo [*] Enabling real-time diagnostic console output...
    python -c "import pathlib; p=pathlib.Path(r'!TARGET_EXE!'); b=bytearray(p.read_bytes()); pe=int.from_bytes(b[0x3c:0x40], 'little'); sub_off=pe+24+68; b[sub_off:sub_off+2]=b'\x03\x00'; p.write_bytes(b); print('[OK] Diagnostic console mode active.')" 2>nul

    echo.
    echo ======================================================================
    echo   LAUNCHING HEMOGLYPH IN CONSOLE DIAGNOSTIC MODE
    echo   (All API errors, OCR logs, and debug info will print below)
    echo ======================================================================
    echo.

    cd /d "!TARGET_DIR!"
    "!TARGET_EXE!"
    set APP_EXIT_CODE=!errorlevel!

    echo.
    echo ======================================================================
    echo   Hemoglyph exited with code: !APP_EXIT_CODE!
    echo ======================================================================

    if exist "!TARGET_DIR!\hemoglyph_startup_error.log" (
        echo.
        echo [!] Found startup crash log:
        type "!TARGET_DIR!\hemoglyph_startup_error.log"
    )

    set /p RESTORE_CHOICE="Switch Hemoglyph.exe back to standard GUI mode (y/n)? "
    if /i "!RESTORE_CHOICE!"=="y" (
        python -c "import pathlib; p=pathlib.Path(r'!TARGET_EXE!'); b=bytearray(p.read_bytes()); pe=int.from_bytes(b[0x3c:0x40], 'little'); sub_off=pe+24+68; b[sub_off:sub_off+2]=b'\x02\x00'; p.write_bytes(b); print('[OK] Standard GUI mode restored.')" 2>nul
    )
    pause
    exit /b !APP_EXIT_CODE!
)

REM 4. If Hemoglyph.exe is not built yet, fallback to running Python source directly
echo [-] Compiled Hemoglyph.exe was not found in common build folders.
echo [*] Checking for source environment (app.py / test_ocr_api.py)...
echo.

if exist "%~dp0app.py" (
    echo [FOUND] Python source file app.py is available.
    echo.
    echo Please select diagnostic action:
    echo   [1] Run full Hemoglyph app in Python console (shows all OCR/API logs)
    echo   [2] Run Vision OCR API tester directly (test_ocr_api.bat)
    echo   [3] Compile Hemoglyph.exe now (build_nuitka.bat)
    echo.
    set /p CHOICE="Enter choice (1, 2, or 3): "
    if "!CHOICE!"=="2" (
        if exist "%~dp0test_ocr_api.bat" (
            call "%~dp0test_ocr_api.bat"
        ) else (
            python "%~dp0test_ocr_api.py"
        )
    ) else if "!CHOICE!"=="3" (
        if exist "%~dp0build_nuitka.bat" (
            call "%~dp0build_nuitka.bat"
        )
    ) else (
        echo.
        echo [*] Launching Python app with full console logging...
        python "%~dp0app.py"
    )
) else (
    echo [ERROR] Neither Hemoglyph.exe nor app.py could be found.
    echo Please run this script inside the project or build folder.
)

pause
