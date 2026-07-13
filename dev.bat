@echo off
chcp 65001 >nul

echo ==========================================
echo   YouTube Downloader - Dev Mode
echo ==========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed
    pause
    exit /b 1
)

REM Install dependencies
echo Installing Python dependencies...
pip install yt-dlp --quiet

REM Check Rust
rustc --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Rust is not installed
    echo Please install from https://rustup.rs
    pause
    exit /b 1
)

REM Install cargo-tauri if needed
cd src-tauri
cargo tauri --version >nul 2>&1
if errorlevel 1 (
    echo Installing cargo-tauri...
    cargo install tauri-cli --version "^1.6"
)

echo.
echo Starting development server...
echo.
cargo tauri dev

cd ..
pause
