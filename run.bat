@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo ================================================
echo Starting Python Downloader
echo ================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found in PATH.
    pause
    exit /b 1
)

echo Installing dependencies for the selected Python interpreter...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Dependency installation failed.
    pause
    exit /b 1
)

echo.
echo Starting application...
python downloader.py
set "APP_RESULT=%errorlevel%"
if not "%APP_RESULT%"=="0" (
    echo.
    echo Application exited with code %APP_RESULT%.
)
pause
exit /b %APP_RESULT%
