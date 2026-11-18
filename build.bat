@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "ROOT=%~dp0"

echo ==========================================
echo   YouTube Downloader - Tauri Build
echo ==========================================
echo.

echo [1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found in PATH.
    goto :fail
)
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Python dependency installation failed.
    goto :fail
)

echo [2/6] Checking Rust toolchain...
rustc --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Rust was not found. Install it from https://rustup.rs
    goto :fail
)
cargo --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Cargo was not found.
    goto :fail
)

echo [3/6] Checking Tauri CLI...
cargo tauri --version >nul 2>&1
if errorlevel 1 (
    echo Installing Tauri CLI 1.x...
    cargo install tauri-cli --version "^1.6"
    if errorlevel 1 (
        echo ERROR: Failed to install Tauri CLI.
        goto :fail
    )
)

echo [4/6] Checking FFmpeg...
if not exist "app\ffmpeg\bin\ffmpeg.exe" (
    echo FFmpeg is missing. Run download_ffmpeg.bat first, then copy
    echo ffmpeg\bin\ffmpeg.exe and ffprobe.exe into app\ffmpeg\bin\.
    if not exist "app\ffmpeg\bin" mkdir "app\ffmpeg\bin"
    if exist "ffmpeg\bin\ffmpeg.exe" copy /Y "ffmpeg\bin\ffmpeg.exe" "app\ffmpeg\bin\ffmpeg.exe" >nul
    if exist "ffmpeg\bin\ffprobe.exe" copy /Y "ffmpeg\bin\ffprobe.exe" "app\ffmpeg\bin\ffprobe.exe" >nul
)
if not exist "app\ffmpeg\bin\ffmpeg.exe" (
    echo WARNING: FFmpeg not found. Video/audio merging and MP3 conversion will be unavailable.
) else (
    echo FFmpeg found.
)

echo [5/6] Checking application icon...
if not exist "app\src-tauri\icons\icon.ico" (
    python app\generate_icon.py
    if errorlevel 1 (
        echo ERROR: Icon generation failed.
        goto :fail
    )
)
if not exist "app\src-tauri\icons\icon.ico" (
    echo ERROR: Required Tauri icon was not created.
    goto :fail
)

echo [6/6] Building Tauri executable...
pushd "app\src-tauri"
cargo tauri build --no-bundle
set "BUILD_RESULT=%errorlevel%"
popd
if not "%BUILD_RESULT%"=="0" (
    echo ERROR: Tauri build failed.
    goto :fail
)

if not exist "app\src-tauri\target\release\downloader.exe" (
    echo ERROR: Build completed but downloader.exe was not found.
    goto :fail
)
copy /Y "app\src-tauri\target\release\downloader.exe" "YouTube Downloader.exe" >nul
if errorlevel 1 (
    echo ERROR: Could not copy the executable.
    goto :fail
)

if exist "app\ffmpeg\bin\ffmpeg.exe" (
    if not exist "ffmpeg\bin" mkdir "ffmpeg\bin"
    copy /Y "app\ffmpeg\bin\ffmpeg.exe" "ffmpeg\bin\ffmpeg.exe" >nul
    if exist "app\ffmpeg\bin\ffprobe.exe" copy /Y "app\ffmpeg\bin\ffprobe.exe" "ffmpeg\bin\ffprobe.exe" >nul
)

echo.
echo BUILD SUCCEEDED: "%ROOT%YouTube Downloader.exe"
echo Note: the Tauri executable still requires Python and yt-dlp on the target machine.
pause
exit /b 0

:fail
echo.
echo BUILD FAILED. No success status was reported.
pause
exit /b 1
