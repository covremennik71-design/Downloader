@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================
echo   YouTube Downloader - Dev Mode
echo ==========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or is not in PATH.
    goto :fail
)

echo Installing Python dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Python dependency installation failed.
    goto :fail
)

rustc --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Rust is not installed. Install it from https://rustup.rs
    goto :fail
)

cargo tauri --version >nul 2>&1
if errorlevel 1 (
    echo Installing Tauri CLI 1.x...
    cargo install tauri-cli --version "^1.6"
    if errorlevel 1 (
        echo ERROR: Tauri CLI installation failed.
        goto :fail
    )
)

pushd "app\src-tauri"
cargo tauri dev
set "DEV_RESULT=%errorlevel%"
popd
if not "%DEV_RESULT%"=="0" goto :fail
exit /b 0

:fail
echo.
echo Development startup failed.
pause
exit /b 1
