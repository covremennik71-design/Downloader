@echo off
setlocal EnableExtensions
title Downloader - Uninstaller
cd /d "%~dp0"

echo ============================================================
echo                 DOWNLOADER UNINSTALLER
echo ============================================================
echo This script can remove build files and optional dependencies.
echo Some dependencies may be shared with other applications.
echo They will only be removed after a separate confirmation.
echo.
echo The source code and this uninstaller will be KEPT.
echo.

choice /c YN /n /m "Remove Downloader build output and local build cache? [Y/N] "
if errorlevel 2 goto :skip_project_files

echo Removing project build output...
if exist "app\src-tauri\target" rmdir /s /q "app\src-tauri\target"
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "__pycache__" rmdir /s /q "__pycache__"
if exist "app\__pycache__" rmdir /s /q "app\__pycache__"
if exist "venv" rmdir /s /q "venv"
if exist ".venv" rmdir /s /q ".venv"
echo Project build output removed.
goto :python_packages

:skip_project_files
echo Project build output kept.

:python_packages
echo.
echo Python packages yt-dlp and customtkinter may be used by other projects.
choice /c YN /n /m "Uninstall yt-dlp and customtkinter from Python 3.12? [Y/N] "
if errorlevel 2 goto :tauri_cli
where py >nul 2>nul
if errorlevel 1 (
  echo Python Launcher not found; skipping Python packages.
) else (
  py -3.12 -m pip uninstall -y yt-dlp customtkinter
)

:tauri_cli
echo.
choice /c YN /n /m "Uninstall the Tauri CLI installed for this user? [Y/N] "
if errorlevel 2 goto :rust
where cargo >nul 2>nul
if errorlevel 1 (
  echo Cargo not found; skipping Tauri CLI.
) else (
  cargo uninstall tauri-cli
)

:rust
echo.
echo WARNING: Rust may be required by other development projects.
choice /c YN /n /m "Uninstall Rust and rustup? [Y/N] "
if errorlevel 2 goto :ffmpeg
where winget >nul 2>nul
if errorlevel 1 (
  echo winget not found; cannot uninstall Rust automatically.
) else (
  winget uninstall --id Rustlang.Rustup -e --source winget --silent
)

:ffmpeg
echo.
echo FFmpeg may be used by other applications.
choice /c YN /n /m "Uninstall FFmpeg installed through winget? [Y/N] "
if errorlevel 2 goto :msvc
where winget >nul 2>nul
if errorlevel 1 (
  echo winget not found; cannot uninstall FFmpeg automatically.
) else (
  winget uninstall --id Gyan.FFmpeg.Shared -e --source winget --silent
)

:msvc
echo.
echo WARNING: Visual Studio Build Tools are shared developer components.
echo Removing them can break builds of unrelated software.
choice /c YN /n /m "Uninstall Visual Studio 2022 Build Tools? [Y/N] "
if errorlevel 2 goto :webview
where winget >nul 2>nul
if errorlevel 1 (
  echo winget not found; cannot uninstall Visual Studio Build Tools.
) else (
  winget uninstall --id Microsoft.VisualStudio.2022.BuildTools -e --source winget
)

:webview
echo.
echo WARNING: WebView2 is used by many Windows applications.
echo It is strongly recommended that you keep it installed.
choice /c YN /n /m "Uninstall Microsoft Edge WebView2 Runtime anyway? [Y/N] "
if errorlevel 2 goto :python_runtime
where winget >nul 2>nul
if errorlevel 1 (
  echo winget not found; cannot uninstall WebView2 automatically.
) else (
  winget uninstall --id Microsoft.EdgeWebView2Runtime -e --source winget
)

:python_runtime
echo.
echo WARNING: Removing Python may break other programs and projects.
choice /c YN /n /m "Uninstall Python 3.12 installed through winget? [Y/N] "
if errorlevel 2 goto :done
where winget >nul 2>nul
if errorlevel 1 (
  echo winget not found; cannot uninstall Python automatically.
) else (
  winget uninstall --id Python.Python.3.12 -e --source winget
)

:done
echo.
echo ============================================================
echo UNINSTALL ROUTINE FINISHED
echo ============================================================
echo Source files were kept. This script does not delete the
echo repository folder, personal downloads, or user data.
echo If the application was installed from an NSIS installer,
echo remove "YouTube Downloader" separately in Windows Settings
echo -^> Apps -^> Installed apps.
echo.
echo Review any winget or pip errors above.
pause
exit /b 0
