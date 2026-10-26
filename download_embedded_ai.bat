@echo off
setlocal enabledelayedexpansion
title HEMOGLYPH - Embedded Offline AI Setup
color 0b

echo ======================================================================
echo   HEMOGLYPH EMBEDDED OFFLINE AI SETUP
echo   Auto-downloading lightweight llama-server engine (17 MB)
echo   and Qwen 2.5 0.5B GGUF model (390 MB) with anti-censorship fallback.
echo ======================================================================
echo.

set SCRIPT_DIR=%~dp0
set BIN_DIR=%SCRIPT_DIR%bin
set MODELS_DIR=%SCRIPT_DIR%models
set TEMP_DIR=%SCRIPT_DIR%temp_ai_setup

if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"
if not exist "%MODELS_DIR%" mkdir "%MODELS_DIR%"
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

REM Detect local VPN / Proxy (v2rayN=10809, Clash=7890, Psiphon=8080)
set PROXY_FLAG=
curl -s --connect-timeout 2 http://127.0.0.1:10809 >nul 2>&1
if not errorlevel 1 (
    echo [*] Detected active v2rayN proxy on 127.0.0.1:10809. Routing traffic...
    set PROXY_FLAG=--proxy http://127.0.0.1:10809
)
if not defined PROXY_FLAG (
    curl -s --connect-timeout 2 http://127.0.0.1:7890 >nul 2>&1
    if not errorlevel 1 (
        echo [*] Detected active Clash proxy on 127.0.0.1:7890. Routing traffic...
        set PROXY_FLAG=--proxy http://127.0.0.1:7890
    )
)

echo [1/3] Downloading lightweight llama-server engine (approx. 17 MB)...
set LLAMA_ZIP=%TEMP_DIR%\llama_bin.zip
set LLAMA_URL=https://github.com/ggml-org/llama.cpp/releases/download/b11193/llama-b11193-bin-win-cpu-x64.zip
set LLAMA_MIRROR=https://ghfast.top/https://github.com/ggml-org/llama.cpp/releases/download/b11193/llama-b11193-bin-win-cpu-x64.zip

curl -L -f %PROXY_FLAG% --connect-timeout 10 -o "%LLAMA_ZIP%" "%LLAMA_URL%"
if errorlevel 1 (
    echo [!] Standard download blocked or timed out. Switching to fast mirror...
    curl -L -f %PROXY_FLAG% --connect-timeout 15 -o "%LLAMA_ZIP%" "%LLAMA_MIRROR%"
)

if not exist "%LLAMA_ZIP%" (
    echo [!] Curl mirror failed. Trying PowerShell with TLS 1.2...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('%LLAMA_MIRROR%', '%LLAMA_ZIP%')"
)

if not exist "%LLAMA_ZIP%" (
    echo.
    echo [ERROR] Could not download llama-server engine automatically due to ISP filtering.
    echo Please download it manually with your browser/IDM from this link:
    echo %LLAMA_URL%
    echo or: %LLAMA_MIRROR%
    echo Extract 'llama-server.exe' and place it inside the 'bin' folder: %BIN_DIR%
    goto :MODEL_STEP
)

echo [2/3] Extracting llama-server.exe into bin/ folder...
powershell -Command "Expand-Archive -Path '%LLAMA_ZIP%' -DestinationPath '%TEMP_DIR%\extracted' -Force"
if exist "%TEMP_DIR%\extracted\llama-server.exe" (
    copy /y "%TEMP_DIR%\extracted\llama-server.exe" "%BIN_DIR%\llama-server.exe" >nul
)
if exist "%TEMP_DIR%\extracted\build\bin\llama-server.exe" (
    copy /y "%TEMP_DIR%\extracted\build\bin\llama-server.exe" "%BIN_DIR%\llama-server.exe" >nul
)
copy /y "%TEMP_DIR%\extracted\*.dll" "%BIN_DIR%\" >nul 2>&1

:MODEL_STEP
echo [3/3] Downloading Qwen 2.5 0.5B GGUF model (approx. 390 MB)...
set MODEL_FILE=%MODELS_DIR%\qwen2.5-0.5b-instruct-q4_k_m.gguf
set MODEL_URL=https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf
set MODEL_MIRROR=https://hf-mirror.com/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf

if exist "%MODEL_FILE%" (
    echo [*] Model file already exists in models/ folder. Skipping.
    goto :SUCCESS
)

echo [*] Connecting to high-speed mirror (hf-mirror.com)...
curl -L -f %PROXY_FLAG% --connect-timeout 10 -o "%MODEL_FILE%" "%MODEL_MIRROR%"
if errorlevel 1 (
    echo [!] Mirror failed. Trying direct HuggingFace...
    curl -L -f %PROXY_FLAG% --connect-timeout 15 -o "%MODEL_FILE%" "%MODEL_URL%"
)

if not exist "%MODEL_FILE%" (
    echo [!] Attempting PowerShell WebClient download...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('%MODEL_MIRROR%', '%MODEL_FILE%')"
)

if not exist "%MODEL_FILE%" (
    echo.
    echo ======================================================================
    echo   [MANUAL DOWNLOAD NEEDED DUE TO ISP RESTRICTIONS]
    echo   Your internet provider is blocking automated curl downloads.
    echo   Please copy this link into your browser or Internet Download Manager:
    echo.
    echo   %MODEL_MIRROR%
    echo   (or: %MODEL_URL%)
    echo.
    echo   Save the downloaded file directly into:
    echo   %MODELS_DIR%\qwen2.5-0.5b-instruct-q4_k_m.gguf
    echo ======================================================================
    pause
    exit /b 1
)

:SUCCESS
rd /s /q "%TEMP_DIR%" >nul 2>&1
echo.
echo ======================================================================
echo   [SUCCESS] EMBEDDED OFFLINE AI ENGINE INSTALLED!
echo   Engine: %BIN_DIR%\llama-server.exe
echo   Model : %MODEL_FILE%
echo.
echo   You can now launch Hemoglyph. The chatbot will start automatically
echo   without requiring Ollama or any extra software!
echo ======================================================================
pause
exit /b 0
