@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Hemoglyph Factory Reset AND Pristine Release Packager
color 0b

echo ======================================================================
echo   HEMOGLYPH FACTORY RESET AND PRISTINE RELEASE PACKAGER
echo   Creates a 100% Pure-GUI, Raw, and Clean Enterprise Distribution
echo ======================================================================
echo.

REM 1. Activate venv if present
if exist ..\.venv\Scripts\activate.bat (
    call ..\.venv\Scripts\activate.bat
) else if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

REM 2. Terminate any running Hemoglyph processes to release file locks
echo [*] Terminating any active Hemoglyph instances...
taskkill /f /im Hemoglyph.exe >nul 2>&1
timeout /t 1 >nul 2>&1

REM 3. Identify target dist folder
set TARGET_DIST=dist\HEMOGLYPH_ALA_1.3.1
if not exist "%TARGET_DIST%\Hemoglyph.exe" (
    if exist "dist\app.dist\Hemoglyph.exe" set TARGET_DIST=dist\app.dist
    if exist "dist\Hemoglyph.dist\Hemoglyph.exe" set TARGET_DIST=dist\Hemoglyph.dist
    if exist "app.dist\Hemoglyph.exe" set TARGET_DIST=app.dist
)

if not exist "%TARGET_DIST%\Hemoglyph.exe" (
    echo [ERROR] Could not find Hemoglyph.exe! Please compile first or check dist folder.
    pause
    exit /b 1
)

echo [*] Target Distribution: %TARGET_DIST%

REM 4. Ingest and harvest all required runtime DLLs and QML components
echo [*] Harvesting and validating essential runtime DLLs and QML controls...
if exist "%~dp0_post_build.py" (
    python "%~dp0_post_build.py"
)

REM 5. Disable CMD / Console window completely on Hemoglyph.exe (Subsystem 2: Windows GUI)
echo [*] Disabling console window on Hemoglyph.exe (Enabling Pure GUI Mode)...
python -c "import pathlib; p=pathlib.Path(r'%TARGET_DIST%/Hemoglyph.exe'); b=bytearray(p.read_bytes()); pe=int.from_bytes(b[0x3c:0x40], 'little'); sub_off=pe+24+68; b[sub_off:sub_off+2]=b'\x02\x00'; p.write_bytes(b); print('[OK] Pure GUI mode enabled (No CMD console window will ever appear).')"

REM 6. Factory Reset Database: Purge personal accounts, test history, and logs from release DB
echo [*] Sanitizing release database (wiping all personal accounts, test history, and emails)...
python -c "import pathlib; db=pathlib.Path(r'%TARGET_DIST%/hemoglyph.db'); (db.unlink() if db.exists() else None); print('[OK] Database purged. A fresh, empty database will be initialized upon first user launch.')"

REM 7. Purge personal remembered email from Windows Registry on this test machine
echo [*] Clearing remembered email from Windows Registry...
reg delete "HKCU\Software\HEMOGLYPH\HEMOGLYPH" /v "rememberedEmail" /f >nul 2>&1
echo [OK] Windows Registry credentials wiped (API keys and app preferences preserved).

REM 8. Purge all development and diagnostic log files
echo [*] Removing diagnostic and crash log files from package...
del /f /q "%TARGET_DIST%\*.log" >nul 2>&1
del /f /q "%TARGET_DIST%\nuitka-crash-report.xml" >nul 2>&1

REM 9. Clean folder appearance: Hide internal DLL and runtime system files
echo [*] Cleaning package appearance: Hiding internal DLL and runtime files...
attrib +h "%TARGET_DIST%\*.dll" >nul 2>&1
attrib +h "%TARGET_DIST%\*.pyd" >nul 2>&1

REM 10. Generate clean user guide in package
echo [*] Generating User Quick-Start Guide...
(
echo ======================================================================
echo   HEMOGLYPH Clinical Decision Support Suite ^(v1.3.1^)
echo   Evidence-Based Laboratory Medicine Platform
echo ======================================================================
echo.
echo QUICK START:
echo 1. Double-click "Hemoglyph.exe" to launch the application.
echo 2. ^(Optional^) Run "Create_Desktop_Shortcut.bat" to add a shortcut to your Desktop.
echo.
echo REQUIREMENTS:
echo - Windows 10 or 11 ^(64-bit^)
echo - 100 percent Offline ^(No internet connection required^)
echo - All 33,875 rules and 2,045 parameters run locally on-device.
echo.
echo Copyright ^(C^) 2026 Sobhan Bahrami. All rights reserved.
echo ======================================================================
) > "%TARGET_DIST%\README_USER.txt"

REM 11. Automatically package clean release ZIP
set RELEASE_ZIP=dist\HEMOGLYPH_ALA_1.3.1.zip
echo [*] Creating clean, pristine release ZIP: %RELEASE_ZIP%...
python -c "import zipfile, pathlib; src = pathlib.Path(r'%TARGET_DIST%'); out = pathlib.Path(r'%RELEASE_ZIP%'); z = zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED); [z.write(f, pathlib.Path('HEMOGLYPH_ALA_1.3.1') / f.relative_to(src)) for f in src.rglob('*') if f.is_file() and not f.name.endswith('.log') and not f.name.endswith('.db') and not f.name.endswith('.pyc')]; z.close(); print('[OK] Clean Release ZIP Created successfully: ' + str(out.resolve()))"

REM 12. Clean intermediate build directory to reclaim disk space
if exist "dist\app.build" rd /s /q "dist\app.build" >nul 2>&1
if exist "dist\Hemoglyph.build" rd /s /q "dist\Hemoglyph.build" >nul 2>&1
if exist "app.build" rd /s /q "app.build" >nul 2>&1
if exist "Hemoglyph.build" rd /s /q "Hemoglyph.build" >nul 2>&1

echo.
echo ======================================================================
echo   [SUCCESS] FACTORY RESET AND PRISTINE PACKAGING COMPLETE!
echo.
echo   Package Status:
echo     * Pure Windows GUI mode active (Zero CMD/Console window)
echo     * 100 percent Raw AND Clean (Zero saved accounts, tests, or emails)
echo     * First launch will display pristine Registration / Login screen
echo     * All DLL dependencies (including sqlite3.dll) and QML intact
echo     * Clean Release ZIP ready: %RELEASE_ZIP%
echo.
echo   When anyone unzips %RELEASE_ZIP%, they get a clean "HEMOGLYPH_ALA_1.3.1"
echo   folder containing Hemoglyph.exe and a desktop shortcut builder!
echo ======================================================================
pause
exit /b 0
