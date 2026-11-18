# Актуальная структура проекта Downloader

Корень проекта — каталог, в котором находятся `README.md`, `downloader.py`, `build.bat` и папка `app/`. Путь к корню не должен быть привязан к имени пользователя или конкретному диску.

```text
Downloader/
├── .github/
│   └── workflows/ci.yml             # CI: Python, JavaScript, Rust/Tauri
├── app/
│   ├── src/                         # Tauri frontend
│   │   ├── index.html
│   │   ├── style.css
│   │   └── main.js
│   ├── src-tauri/                   # Tauri backend
│   │   ├── src/main.rs
│   │   ├── Cargo.toml
│   │   ├── Cargo.lock
│   │   ├── tauri.conf.json
│   │   └── icons/
│   ├── backend/requirements.txt     # Python dependencies for backend reference
│   ├── docs/                        # Project documentation
│   └── generate_icon.py
├── tests/
│   ├── test_url_utils.py
│   ├── test_embedded_scripts.py
│   └── test_runtime_contracts.py
├── downloader.py                    # Standalone CustomTkinter application
├── url_utils.py                     # Shared URL validation for Python GUI
├── config.json
├── requirements.txt
├── Downloader.spec                  # Optional PyInstaller build definition
├── build.bat                        # Tauri executable build
├── dev.bat                          # Tauri development mode
├── run.bat                          # Standalone Python GUI launcher
└── download_ffmpeg.bat              # FFmpeg download into ffmpeg/bin
```

## Два приложения

### Tauri

Поток выполнения:

```text
app/src/index.html + main.js
        │ invoke/listen
        ▼
app/src-tauri/src/main.rs
        │ запускает Python subprocess
        ▼
yt-dlp + optional FFmpeg
```

Tauri использует системный Python и пакет `yt-dlp`. Активный Python-процесс хранится в управляемом состоянии Tauri; команда отмены завершает его. На Windows используется завершение дерева процессов, чтобы не оставлять дочерний FFmpeg-процесс.

### Standalone Python GUI

```text
run.bat
  └── downloader.py
        ├── CustomTkinter
        ├── url_utils.py
        ├── yt-dlp
        └── optional FFmpeg
```

Загрузка и получение метаданных выполняются в фоновых потоках. Обновление Tkinter-виджетов выполняется через callback главного потока.

## Пути и выходные файлы

- Конфигурация использует относительный путь `downloads` по умолчанию.
- Tauri разрешает относительную папку загрузки относительно каталога EXE.
- `download_ffmpeg.bat` размещает FFmpeg в корневом `ffmpeg/bin`.
- `build.bat` при наличии FFmpeg копирует его в `app/ffmpeg/bin` для сборки, а затем рядом с итоговым EXE.
- `build.bat` создаёт `YouTube Downloader.exe` в корне репозитория. Это не полноценный installer и не self-contained Python bundle.

## Команды

Из корня репозитория:

```bat
run.bat
dev.bat
build.bat
download_ffmpeg.bat
```

Ручные Rust-команды:

```bat
cd /d app\src-tauri
cargo check
cargo tauri dev
cargo tauri build --no-bundle
```

## Статус документации

Эта карта отражает текущие пути репозитория. Старые инструкции с `src-tauri/`, `src/`, `backend/` в корне, `dist/` или персональными путями Windows относились к предыдущей структуре и не должны использоваться.
