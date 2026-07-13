@echo off
chcp 65001 >nul
echo ================================================
echo Download FFmpeg for Video+Audio Merging
echo ================================================
echo.

if not exist "ffmpeg" mkdir ffmpeg
if not exist "ffmpeg\bin" mkdir ffmpeg\bin

if exist "ffmpeg\bin\ffmpeg.exe" (
    echo FFmpeg already exists at: ffmpeg\bin\ffmpeg.exe
    echo.
    choice /C YN /M "Re-download? (Y=Yes, N=No)"
    if errorlevel 2 goto :done
)

echo Downloading FFmpeg (this may take a minute)...
echo.

powershell -Command "& { \
    $ProgressPreference = 'SilentlyContinue'; \
    $url = 'https://github.com/BtbN/ffmpeg-builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip'; \
    $out = 'ffmpeg\ffmpeg.zip'; \
    Write-Host 'Downloading from GitHub...'; \
    try { \
        Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing; \
        Write-Host 'Extracting...'; \
        Expand-Archive -Path $out -DestinationPath 'ffmpeg\temp' -Force; \
        $extracted = Get-ChildItem 'ffmpeg\temp' -Directory | Select-Object -First 1; \
        Copy-Item ($extracted.FullName + '\bin\*') -Destination 'ffmpeg\bin\' -Force; \
        Remove-Item 'ffmpeg\temp' -Recurse -Force; \
        Remove-Item $out -Force; \
        Write-Host 'Done!'; \
    } catch { \
        Write-Host 'Auto-download failed!'; \
        Write-Host $_.Exception.Message; \
        exit 1; \
    } \
}"

if %errorlevel% neq 0 (
    echo.
    echo ================================================
    echo AUTO-DOWNLOAD FAILED
    echo ================================================
    echo.
    echo Please download FFmpeg manually:
    echo.
    echo Option 1 (Recommended):
    echo   1. Go to: https://www.gyan.dev/ffmpeg/builds/
    echo   2. Download "ffmpeg-release-essentials.zip"
    echo   3. Extract and copy ffmpeg.exe to:
    echo      %~dp0ffmpeg\bin\ffmpeg.exe
    echo.
    echo Option 2:
    echo   1. Go to: https://github.com/BtbN/FFmpeg-Builds/releases
    echo   2. Download ffmpeg-master-latest-win64-gpl.zip
    echo   3. Extract bin/ffmpeg.exe to:
    echo      %~dp0ffmpeg\bin\ffmpeg.exe
    echo.
) else (
    echo.
    echo ================================================
    echo FFmpeg installed successfully!
    echo ================================================
    echo.
    echo Location: %~dp0ffmpeg\bin\ffmpeg.exe
    echo.
)

:done
echo You can now run build.bat to create the EXE.
echo.
pause
