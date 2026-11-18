# YouTube Downloader

[Русская версия](#русский) · [English](#english)

---

## Русский

### О проекте

YouTube Downloader — настольное приложение для получения информации о видео YouTube и сохранения видео или аудио. В репозитории находятся две реализации:

- **Основное приложение (Tauri):** интерфейс на HTML/CSS/JavaScript находится в `app/src`, а команды приложения и запуск загрузчика — в Rust-коде `app/src-tauri/src/main.rs`. Rust запускает Python и использует библиотеку `yt-dlp`.
- **Отдельная Python-версия:** `downloader.py` — самостоятельный интерфейс на Tkinter/CustomTkinter. Это отдельный вариант приложения, не являющийся частью сборки Tauri.

### Как работает основное приложение

1. Пользователь вставляет ссылку на YouTube.
2. Интерфейс вызывает команду Tauri `get_video_info`.
3. Rust запускает Python-скрипт, который проверяет ссылку и получает сведения о видео через `yt-dlp`.
4. Интерфейс показывает название, канал, длительность и доступные варианты качества.
5. При загрузке команда Tauri `start_download` запускает `yt-dlp` с выбранным форматом и папкой назначения.
6. Python передаёт события прогресса и завершения в stdout; Rust читает их и отправляет интерфейсу события Tauri.
7. Команда `cancel_download` запрашивает остановку активной загрузки.

Для выбора папки и системных диалогов используется Tauri Dialog API.

### Требования

Для сборки основного приложения (Tauri) нужны:

- Windows 10/11 (текущая конфигурация CI и набор иконок ориентированы на Windows).
- Rust toolchain и Cargo.
- Tauri CLI ветки 1.x.
- Python 3 с доступной из командной строки командой `python`.
- Зависимости Python из `app/backend/requirements.txt` (в первую очередь `yt-dlp`).
- Microsoft C++ Build Tools / MSVC и WebView2 Runtime — компоненты среды сборки и запуска Tauri на Windows.
- FFmpeg: необязателен для обычной загрузки видео, но нужен для объединения отдельных видео- и аудиопотоков и извлечения MP3. Приложение ищет `ffmpeg.exe` в нескольких локальных расположениях и в системном PATH.

### Сборка основного приложения (Tauri)

Откройте PowerShell в корне репозитория.

1. Установите Rust, Python 3 и необходимые компоненты Windows для Tauri.
2. Установите Tauri CLI 1.x:

   ```powershell
   cargo install tauri-cli --version "^1.6"
   ```

3. Установите Python-зависимости:

   ```powershell
   python -m pip install -r app/backend/requirements.txt
   ```

4. Перейдите в каталог Rust-приложения и соберите релиз:

   ```powershell
   Set-Location app/src-tauri
   cargo tauri build
   ```

   Для запуска в режиме разработки вместо сборки используйте:

   ```powershell
   cargo tauri dev
   ```

Tauri использует уже подготовленные статические файлы из `app/src`; отдельная команда npm-сборки в текущей конфигурации не задана. Результаты сборки Tauri CLI размещает в каталоге `app/src-tauri/target` (конкретный путь к установщику зависит от платформы и конфигурации сборки).

### FFmpeg

Чтобы обеспечить объединение видео и аудио и конвертацию в MP3, установите FFmpeg и добавьте каталог с `ffmpeg.exe` в PATH либо разместите исполняемый файл в одном из поддерживаемых приложением расположений, например:

- `ffmpeg/bin/ffmpeg.exe` рядом с запускаемым приложением;
- `app/ffmpeg/bin/ffmpeg.exe` при запуске из соответствующего рабочего каталога.

Без FFmpeg доступность максимального качества может быть ограничена одним потоком; извлечение MP3 в Tauri-версии требует FFmpeg.

### Отдельная Python-версия

Для запуска старого самостоятельного Tkinter-интерфейса из корня репозитория:

```powershell
python -m pip install -r requirements.txt
python downloader.py
```

Для сборки этой версии в Windows EXE используется PyInstaller и конфигурация `Downloader.spec`:

```powershell
python -m pip install pyinstaller
python -m PyInstaller --clean --noconfirm Downloader.spec
```

Это отдельный путь сборки; он не собирает Tauri-приложение.

### Конфигурация и данные

- `config.json` в корне используется отдельной Python-версией для настроек и пути загрузки.
- Основное Tauri-приложение сохраняет пользовательские настройки средствами frontend-кода.
- Загружаемые файлы сохраняются в выбранную пользователем папку.
- Не добавляйте личные API-ключи, токены или локальные секреты в Git.

### Проверки в CI

Workflow `.github/workflows/ci.yml` выполняет:
- компиляцию Python-файлов через `python -m compileall -q .`;
- синтаксическую проверку `app/src/main.js` через `node --check`;
- проверку Rust/Tauri через `cargo generate-lockfile --locked` и `cargo check --locked`.

Эти проверки не заменяют полноценный запуск приложения и пробную загрузку на целевой Windows-системе.

### Правовое примечание

Используйте приложение только для материалов, которые вы вправе сохранять. Соблюдайте условия использования YouTube, авторские права и применимое законодательство.

---

## English

### About

YouTube Downloader is a desktop application for retrieving YouTube video information and saving video or audio. The repository contains two implementations:

- **Main application (Tauri):** the HTML/CSS/JavaScript UI is in `app/src`; Tauri commands and downloader process management are implemented in Rust in `app/src-tauri/src/main.rs`. Rust launches Python and uses `yt-dlp`.
- **Standalone Python version:** `downloader.py` is a separate Tkinter/CustomTkinter desktop interface. It is an alternative implementation and is not part of the Tauri build.

### How the main application works

1. The user enters a YouTube URL.
2. The frontend invokes the Tauri `get_video_info` command.
3. Rust runs a Python script that validates the URL and retrieves video metadata with `yt-dlp`.
4. The UI displays the title, channel, duration, and available quality options.
5. When a download starts, the Tauri `start_download` command runs `yt-dlp` with the selected format and destination directory.
6. Python writes progress and completion events to stdout. Rust reads those events and forwards them to the frontend through Tauri events.
7. The `cancel_download` command requests cancellation of the active download.

Folder selection and native dialogs are provided by the Tauri Dialog API.

### Requirements

To build the main Tauri application, install:

- Windows 10/11 (the current CI configuration and icon assets are Windows-oriented).
- The Rust toolchain and Cargo.
- Tauri CLI 1.x.
- Python 3, available on the command line as `python`.
- Python dependencies listed in `app/backend/requirements.txt` (especially `yt-dlp`).
- Microsoft C++ Build Tools / MSVC and the WebView2 Runtime for building and running Tauri on Windows.
- FFmpeg: optional for basic video downloads, but required to merge separate video/audio streams and extract MP3 audio. The application checks several local locations and the system PATH for `ffmpeg.exe`.

### Build the main Tauri application

Open PowerShell in the repository root.

1. Install Rust, Python 3, and the required Windows components for Tauri.
2. Install Tauri CLI 1.x:

   ```powershell
   cargo install tauri-cli --version "^1.6"
   ```

3. Install Python dependencies:

   ```powershell
   python -m pip install -r app/backend/requirements.txt
   ```

4. Enter the Tauri project directory and build the release application:

   ```powershell
   Set-Location app/src-tauri
   cargo tauri build
   ```

   To run the development application instead, use:

   ```powershell
   cargo tauri dev
   ```

The current Tauri configuration points directly to the static frontend in `app/src`; no separate npm build command is configured. Tauri CLI places build outputs under `app/src-tauri/target` (the exact installer path depends on the target platform and build configuration).

### FFmpeg

To merge video and audio streams and convert audio to MP3, install FFmpeg and either add the directory containing `ffmpeg.exe` to PATH or place the executable in a supported location, for example:

- `ffmpeg/bin/ffmpeg.exe` next to the running application;
- `app/ffmpeg/bin/ffmpeg.exe` when running with the corresponding working directory.

Without FFmpeg, the available video quality may be limited to a single stream. MP3 extraction in the Tauri version requires FFmpeg.

### Standalone Python version

To run the separate Tkinter application from the repository root:

```powershell
python -m pip install -r requirements.txt
python downloader.py
```

To package this version as a Windows EXE, use PyInstaller and `Downloader.spec`:

```powershell
python -m pip install pyinstaller
python -m PyInstaller --clean --noconfirm Downloader.spec
```

This is a separate packaging workflow; it does not build the Tauri application.

### Configuration and user data

- The root `config.json` is used by the standalone Python version for settings and the download path.
- The main Tauri application stores user settings through its frontend code.
- Downloaded files are saved to the destination directory selected by the user.
- Do not commit personal API keys, tokens, or local secrets.

### CI checks

The workflow in `.github/workflows/ci.yml` runs:
- Python source compilation using `python -m compileall -q .`;
- JavaScript syntax validation for `app/src/main.js` using `node --check`;
- Rust/Tauri checks using `cargo generate-lockfile --locked` and `cargo check --locked`.

These checks do not replace launching the application and performing a real download test on a target Windows machine.

### Legal note

Only use the application to save content you are authorized to download. Follow YouTube's Terms of Service, copyright rules, and applicable laws.
