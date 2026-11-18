# Установка и запуск Downloader

Эта инструкция соответствует текущей структуре репозитория.

## Требования

- Windows 10/11.
- Python 3.10 или новее, добавленный в PATH.
- Rust toolchain через https://rustup.rs — для Tauri.
- WebView2 Runtime.
- Visual Studio Build Tools с компонентом «Разработка классических приложений на C++» — для сборки Rust/Tauri.
- FFmpeg — необязателен для базовой загрузки, но нужен для объединения отдельных потоков и конвертации в MP3.

## Подготовка

Откройте терминал в корневой папке репозитория — там, где находятся `build.bat`, `dev.bat` и `requirements.txt`.

```bat
python --version
python -m pip install -r requirements.txt
cargo install tauri-cli --version "^1.6"
```

Для установки FFmpeg запустите:

```bat
download_ffmpeg.bat
```

Скрипт сохраняет FFmpeg в `ffmpeg\bin\`. При сборке `build.bat` копирует его в каталог Tauri и рядом с результирующим EXE.

## Запуск Python GUI

```bat
run.bat
```

Либо вручную:

```bat
python -m pip install -r requirements.txt
python downloader.py
```

## Запуск Tauri в режиме разработки

Из корня репозитория:

```bat
dev.bat
```

Скрипт сам переходит в `app\src-tauri\`.

## Сборка Tauri EXE

Из корня репозитория:

```bat
build.bat
```

Результат: `YouTube Downloader.exe` в корне проекта.

**Важно:** текущая сборка Tauri не является полностью автономным установщиком. На целевом компьютере должны быть доступны Python и пакет `yt-dlp`. FFmpeg требуется для объединения отдельных видео- и аудиопотоков и MP3-конвертации. Скрипт сборки проверяет окружение сборочной машины, но не упаковывает системный Python в EXE.

## Типичные проблемы

### Python не найден
Переустановите Python и включите опцию `Add Python to PATH`. Убедитесь, что `python --version` выполняется из нового терминала.

### Rust или Cargo не найден
Установите Rust с https://rustup.rs и перезапустите терминал.

### Не найден WebView2
Установите WebView2 Runtime: https://developer.microsoft.com/en-us/microsoft-edge/webview2/

### Не найден компилятор Windows
Установите Visual Studio Build Tools и компонент «Разработка классических приложений на C++».

### Не найден FFmpeg
Запустите `download_ffmpeg.bat` и проверьте наличие `ffmpeg\bin\ffmpeg.exe`. Без FFmpeg часть вариантов качества и MP3-конвертация недоступны.

### Ручная очистка Rust-сборки
```bat
cd /d app\src-tauri
cargo clean
cd /d ..\..
```

## Проверки перед отправкой изменений

```bat
python -m compileall -q .
python -m unittest discover -s tests -v
node --check app\src\main.js
cargo check --manifest-path app\src-tauri\Cargo.toml
```

Проверка `cargo check` должна выполняться в окружении с установленными Windows/Tauri build dependencies.
