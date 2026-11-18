@echo off
setlocal EnableExtensions
title Downloader - Python setup
cd /d "%~dp0"

echo [1/3] Checking Python 3.12...
where py >nul 2>nul
if errorlevel 1 (
  echo Installing Python 3.12...
  where winget >nul 2>nul || (echo ERROR: winget is missing. Install Microsoft App Installer.& goto :fail)
  winget install --id Python.Python.3.12 -e --source winget --accept-package-agreements --accept-source-agreements
  if errorlevel 1 (echo ERROR: Python installation failed.& goto :fail)
)
py -3.12 --version >nul 2>nul
if errorlevel 1 (
  winget install --id Python.Python.3.12 -e --source winget --accept-package-agreements --accept-source-agreements
  if errorlevel 1 (echo ERROR: Python 3.12 installation failed.& goto :fail)
)
for /f "delims=" %%P in ('py -3.12 -c "import sys; print(sys.executable)"') do set "PYTHON_EXE=%%P"
if not defined PYTHON_EXE (echo ERROR: Could not locate Python 3.12.& goto :fail)
for %%D in ("%PYTHON_EXE%") do set "PYTHON_DIR=%%~dpD"
set "PATH=%PYTHON_DIR%;%PYTHON_DIR%Scripts;%PATH%"

echo [2/3] Updating pip...
py -3.12 -m ensurepip --upgrade
if errorlevel 1 (echo ERROR: ensurepip failed.& goto :fail)
py -3.12 -m pip install --upgrade pip
if errorlevel 1 (echo ERROR: pip update failed.& goto :fail)

echo [3/3] Installing project dependencies...
py -3.12 -m pip install --upgrade -r "%~dp0requirements.txt"
if errorlevel 1 (echo ERROR: Root requirements failed.& goto :fail)
py -3.12 -m pip install --upgrade -r "%~dp0app\backend\requirements.txt"
if errorlevel 1 (echo ERROR: Backend requirements failed.& goto :fail)

echo SUCCESS: Python 3.12 and project dependencies are ready.
echo Python: %PYTHON_EXE%
pause
exit /b 0
:fail
echo SETUP FAILED. No success status was reported.
pause
exit /b 1
