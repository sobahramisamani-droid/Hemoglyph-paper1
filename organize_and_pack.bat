@echo off
setlocal
cd /d "%~dp0"
title Hemoglyph Structure Organizer and Clean Packager
color 0b

echo ======================================================================
echo   HEMOGLYPH RELEASE STRUCTURE ORGANIZER AND CLEAN PACKAGER
echo   Organizes all 23 Python folders and DLLs into a clean 'bin' subfolder
echo ======================================================================
echo.

echo [*] Closing any open Hemoglyph instances...
taskkill /f /im Hemoglyph.exe >nul 2>&1
taskkill /f /im Hemoglyph_App.exe >nul 2>&1
timeout /t 1 >nul 2>&1

set "PYFILE=%TEMP%\organize_hg.py"

echo import os, sys, shutil, pathlib, zipfile > "%PYFILE%"
echo dist = pathlib.Path(r"dist") >> "%PYFILE%"
echo src = dist / "HEMOGLYPH_ALA_1.3.1" >> "%PYFILE%"
echo if not (src / "Hemoglyph.exe").exists(): >> "%PYFILE%"
echo     src = dist / "app.dist" >> "%PYFILE%"
echo if not (src / "Hemoglyph.exe").exists(): >> "%PYFILE%"
echo     print("[ERROR] Could not find Hemoglyph.exe in dist folder!"); sys.exit(1) >> "%PYFILE%"
echo stage = dist / "CLEAN_STAGE" >> "%PYFILE%"
echo if stage.exists(): shutil.rmtree(stage, ignore_errors=True) >> "%PYFILE%"
echo bin_d = stage / "bin" >> "%PYFILE%"
echo bin_d.mkdir(parents=True, exist_ok=True) >> "%PYFILE%"
echo print("[*] Moving 23 folders and DLLs into clean 'bin' subfolder...") >> "%PYFILE%"
echo for d in os.listdir(src): >> "%PYFILE%"
echo     p = src / d >> "%PYFILE%"
echo     if p.name.endswith(".log") or p.name == "hemoglyph.db" or p.name.endswith(".zip"): continue >> "%PYFILE%"
echo     dest = bin_d / p.name >> "%PYFILE%"
echo     if p.is_dir(): shutil.copytree(p, dest, dirs_exist_ok=True) >> "%PYFILE%"
echo     else: shutil.copy2(p, dest) >> "%PYFILE%"
echo vbs = 'Set W = CreateObject("WScript.Shell")\nP = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)\nW.CurrentDirectory = P + "\\bin"\nW.Run chr(34) + P + "\\bin\\Hemoglyph.exe" + chr(34), 0, False\n' >> "%PYFILE%"
echo (stage / "Hemoglyph.vbs").write_text(vbs, encoding="utf-8") >> "%PYFILE%"
echo bat = '@echo off\ncd /d "%%~dp0bin"\nstart "" "%%~dp0bin\\Hemoglyph.exe"\n' >> "%PYFILE%"
echo (stage / "Run_Hemoglyph.bat").write_text(bat, encoding="utf-8") >> "%PYFILE%"
echo if pathlib.Path("Create_Desktop_Shortcut.bat").exists(): shutil.copy2("Create_Desktop_Shortcut.bat", stage / "Create_Desktop_Shortcut.bat") >> "%PYFILE%"
echo elif (src / "Create_Desktop_Shortcut.bat").exists(): shutil.copy2(src / "Create_Desktop_Shortcut.bat", stage / "Create_Desktop_Shortcut.bat") >> "%PYFILE%"
echo readme = "======================================================================\nHEMOGLYPH Clinical Decision Support Suite (v1.3.1)\nEvidence-Based Laboratory Medicine Platform\n======================================================================\n\nHOW TO RUN:\n1. Double-click 'Hemoglyph.vbs' or 'Run_Hemoglyph.bat' to start.\n2. Run 'Create_Desktop_Shortcut.bat' to create a desktop shortcut.\n\nREQUIREMENTS:\n- Windows 10 or 11 (64-bit)\n- 100%% Offline (No cloud connection required)\n- All 33,875 rules and 2,045 parameters run locally on-device.\n\nCopyright (C) 2026 Sobhan Bahrami. All rights reserved.\n======================================================================\n" >> "%PYFILE%"
echo (stage / "README.txt").write_text(readme, encoding="utf-8") >> "%PYFILE%"
echo out = dist / "HEMOGLYPH_ALA_1.3.1.zip" >> "%PYFILE%"
echo print("[*] Creating organized ZIP file: " + str(out.resolve()) + "...") >> "%PYFILE%"
echo with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z: >> "%PYFILE%"
echo     for f in stage.rglob("*"): >> "%PYFILE%"
echo         if f.is_file(): z.write(f, pathlib.Path("HEMOGLYPH_ALA_1.3.1") / f.relative_to(stage)) >> "%PYFILE%"
echo shutil.rmtree(stage, ignore_errors=True) >> "%PYFILE%"
echo sz = out.stat().st_size / (1024 * 1024) >> "%PYFILE%"
echo print("[SUCCESS] Organized ZIP Created: " + str(out.resolve()) + " (" + str(round(sz, 1)) + " MB)") >> "%PYFILE%"

python "%PYFILE%"
del /f /q "%PYFILE%" >nul 2>&1

echo.
echo ======================================================================
echo   Done! All 23 folders and DLLs are now organized in 'bin'.
echo   The clean ZIP file is ready in the 'dist' folder with Desktop Shortcut!
echo ======================================================================
pause
