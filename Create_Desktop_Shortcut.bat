@echo off
setlocal
cd /d "%~dp0"
title Hemoglyph - Desktop Shortcut
set "APP_NAME=Hemoglyph CDSS"
set "DESC=Hemoglyph Clinical Decision Support Suite 1.3.1"

REM --- locate the executable (flat layout, or bin\ layout from _organize_release) ---
set "EXE="
if exist "%~dp0Hemoglyph.exe"       set "EXE=%~dp0Hemoglyph.exe"
if not defined EXE if exist "%~dp0bin\Hemoglyph.exe"   set "EXE=%~dp0bin\Hemoglyph.exe"
if not defined EXE (
    echo [ERROR] Hemoglyph.exe not found next to this script.
    pause
    exit /b 1
)
for %%F in ("%EXE%") do set "WORKDIR=%%~dpF"
set "WORKDIR=%WORKDIR:~0,-1%"

REM --- icon: prefer the .ico file, fall back to the icon embedded in the exe ---
set "ICON=%EXE%,0"
if exist "%WORKDIR%\app_icon.ico" set "ICON=%WORKDIR%\app_icon.ico,0"

REM --- 1) PowerShell (always present on Win10/11, not blocked by WSH policies) ---
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$s=(New-Object -ComObject WScript.Shell);" ^
  "$d=[Environment]::GetFolderPath('Desktop');" ^
  "$l=$s.CreateShortcut((Join-Path $d '%APP_NAME%.lnk'));" ^
  "$l.TargetPath='%EXE%';$l.WorkingDirectory='%WORKDIR%';$l.IconLocation='%ICON%';$l.Description='%DESC%';$l.WindowStyle=1;$l.Save();" ^
  "$m=Join-Path ([Environment]::GetFolderPath('Programs')) 'Hemoglyph';" ^
  "New-Item -ItemType Directory -Force -Path $m | Out-Null;" ^
  "$l2=$s.CreateShortcut((Join-Path $m '%APP_NAME%.lnk'));" ^
  "$l2.TargetPath='%EXE%';$l2.WorkingDirectory='%WORKDIR%';$l2.IconLocation='%ICON%';$l2.Description='%DESC%';$l2.Save();" ^
  "exit 0" >nul 2>&1
if not errorlevel 1 goto :DONE

REM --- 2) Fallback: Windows Script Host ---
set "VBS=%TEMP%\hemoglyph_lnk.vbs"
> "%VBS%" echo Set oWS = WScript.CreateObject("WScript.Shell")
>>"%VBS%" echo sLink = oWS.SpecialFolders("Desktop") ^& "\%APP_NAME%.lnk"
>>"%VBS%" echo Set oL = oWS.CreateShortcut(sLink)
>>"%VBS%" echo oL.TargetPath = "%EXE%"
>>"%VBS%" echo oL.WorkingDirectory = "%WORKDIR%"
>>"%VBS%" echo oL.IconLocation = "%ICON%"
>>"%VBS%" echo oL.Description = "%DESC%"
>>"%VBS%" echo oL.Save
cscript //nologo "%VBS%"
set "RC=%errorlevel%"
del /f /q "%VBS%" >nul 2>&1
if not "%RC%"=="0" (
    echo [ERROR] Could not create the shortcut. Right-click Hemoglyph.exe ^> Send to ^> Desktop (create shortcut).
    pause
    exit /b 1
)

:DONE
REM refresh the icon cache so the new icon shows immediately
ie4uinit.exe -show >nul 2>&1
echo [OK] "%APP_NAME%" shortcut created on the Desktop and in the Start Menu.
echo      Target: %EXE%
timeout /t 4 >nul
exit /b 0
