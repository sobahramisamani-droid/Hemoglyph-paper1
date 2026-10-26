#!/usr/bin/env python3
"""
HEMOGLYPH Release Structure Organizer & Clean Packager
Moves all internal DLLs, Python modules, and binaries into a clean 'bin' subfolder
Leaves only clean launchers and user documentation at the root.
"""

import os
import sys
import shutil
import pathlib
import zipfile

def main():
    print("======================================================================")
    print("  HEMOGLYPH RELEASE STRUCTURE ORGANIZER AND CLEAN PACKAGER")
    print("  Organizes all 23 Python folders and DLLs into a clean 'bin' subfolder")
    print("======================================================================")

    # 1. Terminate any running Hemoglyph processes to release file locks
    if sys.platform == "win32":
        print("[*] Closing any active Hemoglyph instances to unlock files...")
        os.system("taskkill /f /im Hemoglyph.exe >nul 2>&1")
        os.system("taskkill /f /im Hemoglyph_App.exe >nul 2>&1")

    # 2. Identify source build folder
    candidates = [
        pathlib.Path("dist/HEMOGLYPH_ALA_1.3.1"),
        pathlib.Path("dist/app.dist"),
        pathlib.Path("dist/Hemoglyph.dist"),
        pathlib.Path("dist/Hemoglyph"),
        pathlib.Path("dist"),
        pathlib.Path("HEMOGLYPH_ALA_1.3.1"),
        pathlib.Path("app.dist"),
    ]
    src_dir = None
    for cand in candidates:
        if (cand / "Hemoglyph.exe").exists():
            src_dir = cand
            break

    if not src_dir:
        print("[ERROR] Could not find Hemoglyph.exe in any dist folder!")
        return 1

    print(f"[*] Source directory: {src_dir.resolve()}")

    # 3. Prepare staging folder
    dist_root = src_dir.parent
    stage_dir = dist_root / "HEMOGLYPH_CLEAN_STAGE"
    if stage_dir.exists():
        shutil.rmtree(stage_dir, ignore_errors=True)

    bin_dir = stage_dir / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)

    # 4. Copy all internal dependencies, DLLs, and Python folders into bin/
    print("[*] Moving all 23 Python packages and DLLs into clean 'bin' subfolder...")
    for item in src_dir.iterdir():
        if item.name.endswith(".log") or item.name == "hemoglyph.db" or item.name == "nuitka-crash-report.xml":
            continue
        dest = bin_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)

    # 5. Create root silent VBS launcher (Pure GUI, Zero CMD)
    vbs_content = (
        'Set WshShell = CreateObject("WScript.Shell")\n'
        'strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)\n'
        'WshShell.CurrentDirectory = strPath & "\\bin"\n'
        'WshShell.Run """" & strPath & "\\bin\\Hemoglyph.exe""", 0, False\n'
    )
    (stage_dir / "Hemoglyph.vbs").write_text(vbs_content, encoding="utf-8")

    # 6. Create root BAT launcher
    bat_content = (
        '@echo off\n'
        'cd /d "%~dp0bin"\n'
        'start "" "%~dp0bin\\Hemoglyph.exe"\n'
    )
    (stage_dir / "Run_Hemoglyph.bat").write_text(bat_content, encoding="utf-8")

    # 7. Create root Desktop Shortcut maker
    if pathlib.Path("Create_Desktop_Shortcut.bat").exists():
        shutil.copy2("Create_Desktop_Shortcut.bat", stage_dir / "Create_Desktop_Shortcut.bat")
    else:
        shortcut_maker = (
            '@echo off\n'
            'setlocal\n'
            'cd /d "%~dp0"\n'
            'set VBS="%TEMP%\\make_hg_lnk.vbs"\n'
            'echo Set oWS = WScript.CreateObject("WScript.Shell") > %VBS%\n'
            'echo sLink = oWS.SpecialFolders("Desktop") ^& "\\Hemoglyph CDSS.lnk" >> %VBS%\n'
            'echo Set oL = oWS.CreateShortcut(sLink) >> %VBS%\n'
            'echo oL.TargetPath = "%~dp0bin\\Hemoglyph.exe" >> %VBS%\n'
            'echo oL.WorkingDirectory = "%~dp0bin" >> %VBS%\n'
            'echo oL.Description = "Hemoglyph Clinical Decision Support Suite" >> %VBS%\n'
            'if exist "%~dp0bin\\app_icon.ico" (\n'
            '    echo oL.IconLocation = "%~dp0bin\\app_icon.ico, 0" >> %VBS%\n'
            ')\n'
            'echo oL.Save >> %VBS%\n'
            'cscript /nologo %VBS%\n'
            'del /f /q %VBS% >nul 2>&1\n'
            'echo [*] Desktop Shortcut created successfully: "Hemoglyph CDSS" on your Desktop!\n'
            'timeout /t 3 >nul\n'
        )
        (stage_dir / "Create_Desktop_Shortcut.bat").write_text(shortcut_maker, encoding="utf-8")

    # 7B. SECURITY: never ship .env (contains API keys). Ship only the template,
    #     and purge any .env that slipped into the copied bin/ folder.
    for leaked in [bin_dir / ".env", bin_dir / "test_ocr_api.py", bin_dir / "test_ocr_api.bat"]:
        if leaked.exists():
            leaked.unlink()
    if pathlib.Path(".env.example").exists():
        shutil.copy2(".env.example", bin_dir / ".env.example")

    # 8. Create User Guide
    guide_content = (
        "======================================================================\n"
        "  HEMOGLYPH Clinical Decision Support Suite (v1.3.1)\n"
        "  Evidence-Based Laboratory Medicine Platform\n"
        "======================================================================\n\n"
        "HOW TO RUN:\n"
        "1. Double-click 'Run_Hemoglyph.bat' (or bin\\Hemoglyph.exe) to start the application.\n"
        "2. (Optional) Run 'Create_Desktop_Shortcut.bat' to create a desktop shortcut.\n\n"
        "REQUIREMENTS:\n"
        "- Windows 10 or 11 (64-bit)\n"
        "- All 33,230 rules, 2,045 lab parameters and 100 risk models run locally on-device.\n"
        "- Optional cloud Vision OCR (Groq/OpenRouter) needs an API key in bin\\.env\n"
        "  (copy bin\\.env.example to bin\\.env). Without it, local Tesseract OCR is used.\n"
        "- AI Copilot chat is disabled in v1.3.1.\n\n"
        "Copyright (C) 2026 Sobhan Bahrami. All rights reserved.\n"
        "======================================================================\n"
    )
    (stage_dir / "README.txt").write_text(guide_content, encoding="utf-8")

    # 9. Package into clean final ZIP
    out_zip = dist_root / "HEMOGLYPH_ALA_1.3.1.zip"
    print(f"[*] Packaging organized release into: {out_zip.resolve()}...")
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for f in stage_dir.rglob("*"):
            if f.is_file():
                z.write(f, pathlib.Path("HEMOGLYPH_ALA_1.3.1") / f.relative_to(stage_dir))

    # 10. Clean up staging folder
    shutil.rmtree(stage_dir, ignore_errors=True)

    size_mb = out_zip.stat().st_size / (1024 * 1024)
    print("\n======================================================================")
    print(f"[SUCCESS] ORGANIZED RELEASE PACKAGE READY: {out_zip.name} ({size_mb:.1f} MB)")
    print(f"[SUCCESS] File Location: {out_zip.resolve()}")
    print("\nClean Folder Structure inside the ZIP:")
    print("  HEMOGLYPH_ALA_1.3.1/")
    print("    ├── Hemoglyph.vbs               <-- Silent Launcher (Zero CMD)")
    print("    ├── Run_Hemoglyph.bat           <-- Quick Launcher")
    print("    ├── Create_Desktop_Shortcut.bat <-- Desktop Shortcut Builder")
    print("    ├── README.txt                  <-- User Guide")
    print("    └── bin/                        <-- Clean subfolder with all DLLs and PySide6")
    print("\nThe root is 100% clean and uncluttered!")
    print("======================================================================")
    return 0

if __name__ == "__main__":
    sys.exit(main())
