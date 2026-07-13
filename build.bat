@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo   YouTube Downloader - Build Script
echo   Tauri + Python Edition
echo ==========================================
echo.

:: [1/8] Checking Python installation
echo [1/8] Checking Python installation...
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)
echo OK: Python found

:: [2/8] Fixing pip warnings and installing dependencies
echo [2/8] Installing Python dependencies...
for /d %%i in ("%LOCALAPPDATA%\Programs\Python\Python314\Lib\site-packages\~*") do rmdir /s /q "%%i" 2>nul
pip install --upgrade --force-reinstall yt-dlp --quiet
echo OK: Python dependencies installed

:: [3/8] Checking Rust installation
echo [3/8] Checking Rust installation...
rustc --version >nul 2>&1
if !errorlevel! neq 0 (
    echo ERROR: Rust not found!
    pause
    exit /b 1
)
echo OK: Rust found

:: [4/8] Checking Tauri CLI
echo [4/8] Checking Tauri CLI...
cargo tauri --version >nul 2>&1
if !errorlevel! neq 0 (
    echo Tauri CLI not found. Installing...
    cargo install tauri-cli
    if !errorlevel! neq 0 (
        echo ERROR: Failed to install Tauri CLI
        pause
        exit /b 1
    )
)
echo OK: Tauri CLI ready

:: [5/8] Downloading FFmpeg (CRITICAL FOR VIDEO+AUDIO MERGING)
echo [5/8] Downloading FFmpeg...
if not exist "app\ffmpeg" mkdir "app\ffmpeg"
if not exist "app\ffmpeg\bin\ffmpeg.exe" (
    echo FFmpeg not found. Downloading...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip' -OutFile 'app\ffmpeg.zip'}"
    if !errorlevel! neq 0 (
        echo ERROR: Failed to download FFmpeg
        pause
        exit /b 1
    )
    echo Extracting FFmpeg...
    powershell -Command "& {Expand-Archive -Path 'app\ffmpeg.zip' -DestinationPath 'app\ffmpeg' -Force}"
    if !errorlevel! neq 0 (
        echo ERROR: Failed to extract FFmpeg
        pause
        exit /b 1
    )
    :: Move files to correct location
    if exist "app\ffmpeg\ffmpeg-master-latest-win64-gpl\bin" (
        move "app\ffmpeg\ffmpeg-master-latest-win64-gpl\bin" "app\ffmpeg\bin" >nul
        rmdir /s /q "app\ffmpeg\ffmpeg-master-latest-win64-gpl" >nul
    )
    del "app\ffmpeg.zip" >nul 2>&1
)
echo OK: FFmpeg ready

:: [6/8] Generating Icon
echo [6/8] Checking application icon...
if not exist "app\src-tauri\icons" mkdir "app\src-tauri\icons"
if not exist "app\src-tauri\icons\icon.ico" (
    echo Icon not found. Generating...
    python app\generate_icon.py
)
echo OK: Icon ready

:: [7/8] Building Tauri application
echo [7/8] Building Tauri application...
cd app\src-tauri
cargo build --release
if !errorlevel! neq 0 (
    echo ERROR: Build failed!
    cd ..\..
    pause
    exit /b 1
)
cd ..\..

:: [8/8] Copying EXE and FFmpeg to root
echo [8/8] Copying files to root...
copy /Y "app\src-tauri\target\release\downloader.exe" "YouTube Downloader.exe" >nul
if not exist "ffmpeg" mkdir "ffmpeg"
if not exist "ffmpeg\bin" mkdir "ffmpeg\bin"
copy /Y "app\ffmpeg\bin\ffmpeg.exe" "ffmpeg\bin\ffmpeg.exe" >nul
copy /Y "app\ffmpeg\bin\ffprobe.exe" "ffmpeg\bin\ffprobe.exe" >nul

echo.
echo ==========================================
echo   BUILD SUCCESSFUL!
echo   EXE location: YouTube Downloader.exe
echo   FFmpeg location: ffmpeg\bin\
echo ==========================================
pause