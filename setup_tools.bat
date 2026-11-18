@echo off
setlocal EnableExtensions
title Downloader - Build tools setup
cd /d "%~dp0"

echo [1/5] Checking winget...
where winget >nul 2>nul || (echo ERROR: Install Microsoft App Installer / winget first.& goto :fail)

echo [2/5] Checking Rust...
if not exist "%USERPROFILE%\.cargo\bin\rustc.exe" (
  winget install --id Rustlang.Rustup -e --source winget --accept-package-agreements --accept-source-agreements
  if errorlevel 1 (echo ERROR: Rust installation failed.& goto :fail)
)
set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
where rustc >nul 2>nul || (echo ERROR: Rust not visible. Reopen terminal and rerun.& goto :fail)
rustc --version
where rustup >nul 2>nul && rustup update stable
if errorlevel 1 (echo WARNING: Rust toolchain update was skipped or failed; continuing with installed compiler.)

echo [3/5] Checking MSVC C++ Build Tools...
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
set "VSROOT="
if exist "%VSWHERE%" (
  "%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath > "%TEMP%\downloader_vs.txt"
  set /p VSROOT=<"%TEMP%\downloader_vs.txt"
)
if not defined VSROOT (
  echo Installing Visual Studio 2022 Build Tools and C++ workload. This is a large download...
  winget install --id Microsoft.VisualStudio.2022.BuildTools -e --source winget --override "--wait --quiet --norestart --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended" --accept-package-agreements --accept-source-agreements
  if errorlevel 1 (echo ERROR: MSVC installation failed.& goto :fail)
  if exist "%VSWHERE%" (
    "%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath > "%TEMP%\downloader_vs.txt"
    set /p VSROOT=<"%TEMP%\downloader_vs.txt"
  )
)
if not defined VSROOT (echo ERROR: MSVC not detected. Reboot and rerun setup_tools.bat.& goto :fail)

echo [4/5] Checking WebView2 Runtime...
reg query "HKLM\SOFTWARE\Microsoft\EdgeUpdate\Clients" /s /f "Microsoft Edge WebView2" >nul 2>nul
if errorlevel 1 (
  winget install --id Microsoft.EdgeWebView2Runtime -e --source winget --accept-package-agreements --accept-source-agreements
  if errorlevel 1 (echo ERROR: WebView2 installation failed.& goto :fail)
)

echo [5/5] Checking FFmpeg and Tauri CLI...
where ffmpeg >nul 2>nul
if errorlevel 1 (
  winget install --id Gyan.FFmpeg.Shared -e --source winget --accept-package-agreements --accept-source-agreements
  if errorlevel 1 (echo ERROR: FFmpeg installation failed.& goto :fail)
)
where ffmpeg >nul 2>nul || (echo FFmpeg PATH not refreshed. Reopen terminal and rerun.& goto :fail)

set "TAURI_VERSION="
for /f "tokens=*" %%V in ('cargo tauri --version 2^>nul') do set "TAURI_VERSION=%%V"
echo %TAURI_VERSION% | findstr /c:"1.6.6" >nul
if errorlevel 1 (
  echo Installing or updating pinned Tauri CLI 1.6.6...
  cargo install tauri-cli --version 1.6.6 --locked --force
  if errorlevel 1 (echo ERROR: Tauri CLI installation failed.& goto :fail)
)
cargo tauri --version
if errorlevel 1 (echo ERROR: Tauri CLI unavailable.& goto :fail)

echo SUCCESS: Rust, MSVC, WebView2, FFmpeg and Tauri CLI are ready.
echo Run setup_python.bat first, then build.bat.
pause
exit /b 0
:fail
echo SETUP FAILED. No success status was reported.
pause
exit /b 1
