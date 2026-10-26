@echo off
setlocal
cd /d "%~dp0"
echo [*] Cleaning folder view: Hiding internal DLL and runtime system files...

attrib +h *.dll >nul 2>&1
attrib +h *.pyd >nul 2>&1
attrib +h *.dist-info >nul 2>&1
attrib +h *.egg-info >nul 2>&1

echo [OK] Folder view cleaned! Only Hemoglyph.exe and user shortcuts are now visible.
