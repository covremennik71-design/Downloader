@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "FFMPEG_ROOT=%~dp0ffmpeg"
set "ZIP_FILE=%~dp0ffmpeg-download.zip"
set "TEMP_DIR=%~dp0ffmpeg-temp"

echo ================================================
echo Download FFmpeg for video/audio processing
echo ================================================
echo.

if exist "%FFMPEG_ROOT%\bin\ffmpeg.exe" (
    echo FFmpeg already exists at "%FFMPEG_ROOT%\bin\ffmpeg.exe".
    choice /C YN /M "Re-download? (Y=Yes, N=No)"
    if errorlevel 2 goto :done
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; $url='https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip'; $zip='%ZIP_FILE%'; $temp='%TEMP_DIR%'; $dest='%FFMPEG_ROOT%\bin'; try { Invoke-WebRequest -Uri $url -OutFile $zip; if (Test-Path $temp) { Remove-Item $temp -Recurse -Force }; Expand-Archive -LiteralPath $zip -DestinationPath $temp -Force; $root=Get-ChildItem -LiteralPath $temp -Directory | Select-Object -First 1; if (-not $root) { throw 'Archive has no root directory' }; $bin=Join-Path $root.FullName 'bin'; if (-not (Test-Path (Join-Path $bin 'ffmpeg.exe'))) { throw 'ffmpeg.exe not found in archive' }; New-Item -ItemType Directory -Force -Path $dest | Out-Null; Copy-Item -Path (Join-Path $bin '*') -Destination $dest -Force; if (-not (Test-Path (Join-Path $dest 'ffmpeg.exe'))) { throw 'FFmpeg copy verification failed' }; Remove-Item $temp -Recurse -Force; Remove-Item $zip -Force; Write-Host 'FFmpeg installed and verified.' } catch { Write-Error $_; exit 1 }"
if errorlevel 1 (
    echo.
    echo FFmpeg download or extraction failed.
    echo Download it manually from https://www.gyan.dev/ffmpeg/builds/
    echo Extract ffmpeg.exe and ffprobe.exe into "%FFMPEG_ROOT%\bin".
    if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%"
    if exist "%ZIP_FILE%" del /q "%ZIP_FILE%"
    goto :fail
)

:done
echo.
echo FFmpeg location: "%FFMPEG_ROOT%\bin\ffmpeg.exe"
pause
exit /b 0

:fail
pause
exit /b 1
