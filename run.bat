@echo off
chcp 65001 >nul
echo ================================================
echo Starting Downloader
echo ================================================
echo.

echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo.

echo Starting application...
python downloader.py
pause
