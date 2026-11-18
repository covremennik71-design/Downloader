@echo off
setlocal EnableExtensions
title Downloader - Build
cd /d "%~dp0"

echo Select build type:
echo   1. Portable EXE
echo   2. NSIS installer
echo   3. Both
choice /c 123 /n /m "Choose 1, 2 or 3: "
set "BUILD_MODE=%ERRORLEVEL%"

set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
where cargo >nul 2>nul || (echo ERROR: Run setup_tools.bat.& goto :fail)
where py >nul 2>nul || (echo ERROR: Run setup_python.bat.& goto :fail)
py -3.12 -c "import yt_dlp" >nul 2>nul || (echo ERROR: Run setup_python.bat.& goto :fail)
where ffmpeg >nul 2>nul || (echo ERROR: Run setup_tools.bat.& goto :fail)
if not exist "app\src-tauri\tauri.conf.json" (echo ERROR: Tauri project files missing.& goto :fail)
cargo tauri --version >nul 2>nul || (echo ERROR: Run setup_tools.bat.& goto :fail)

pushd "app\src-tauri"
if "%BUILD_MODE%"=="1" goto :portable
if "%BUILD_MODE%"=="2" goto :installer
goto :both

:portable
echo Building optimized release EXE...
cargo build --release --locked
if errorlevel 1 (popd& echo ERROR: EXE compilation failed.& goto :fail)
if not exist "target\release\downloader.exe" (popd& echo ERROR: Expected EXE missing.& goto :fail)
if not exist "..\..\dist" mkdir "..\..\dist"
copy /y "target\release\downloader.exe" "..\..\dist\Downloader.exe" >nul
if errorlevel 1 (popd& echo ERROR: Copy failed.& goto :fail)
popd
echo SUCCESS: dist\Downloader.exe created.
echo NOTE: Current app invokes system Python and yt-dlp at runtime. They are not embedded in this EXE.
goto :done

:installer
echo Building NSIS installer...
cargo tauri build --bundles nsis
if errorlevel 1 (popd& echo ERROR: NSIS build failed.& goto :fail)
popd
goto :show

:both
echo Building optimized release EXE...
cargo build --release --locked
if errorlevel 1 (popd& echo ERROR: EXE compilation failed.& goto :fail)
if not exist "..\..\dist" mkdir "..\..\dist"
copy /y "target\release\downloader.exe" "..\..\dist\Downloader.exe" >nul
if errorlevel 1 (popd& echo ERROR: Copy failed.& goto :fail)
echo Building NSIS installer...
cargo tauri build --bundles nsis
if errorlevel 1 (popd& echo ERROR: NSIS build failed.& goto :fail)
popd
goto :show

:show
echo Installer output: app\src-tauri\target\release\bundle\nsis\
echo Portable EXE: dist\Downloader.exe
goto :done

:done
echo BUILD COMPLETED. Verify output files before distribution.
pause
exit /b 0
:fail
echo BUILD FAILED. No success status was reported.
pause
exit /b 1
