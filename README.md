# YouTube Downloader

Десктопное приложение для загрузки видео и аудио с YouTube. Два варианта запуска:

- **Tauri** — современный UI (HTML/CSS/JS + Rust backend)
- **Python** — standalone GUI на customtkinter

## Быстрый старт

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/covremennik71-design/Downloader.git
cd Downloader
```

### 2. Установите зависимости

```bash
pip install -r requirements.txt
```

### 3. Настройте папку загрузки (необязательно)

По умолчанию файлы сохраняются в папку `downloads` рядом с приложением. Папку можно изменить в настройках или через поле выбора каталога. Путь по умолчанию больше не привязан к компьютеру разработчика.

Ключ YouTube Data API для обычной загрузки через yt-dlp не требуется.

### 4. Запуск

**Python (standalone):**
```bash
python downloader.py
```

**Tauri (сборка EXE):**
```bash
build.bat
```

## Структура проекта

```
Downloader/
├── downloader.py          ← Standalone Python загрузчик (customtkinter GUI)
├── config.json            ← Конфигурация (API ключ, путь, тема)
├── requirements.txt       ← Python зависимости
├── build.bat              ← Скрипт сборки Tauri EXE
├── dev.bat                ← Запуск Tauri в dev-режиме
├── run.bat                ← Запуск Python версии
├── download_ffmpeg.bat    ← Скачать ffmpeg автоматически
├── Downloader.spec        ← Конфигурация PyInstaller
│
├── ffmpeg/bin/            ← ffmpeg.exe, ffprobe.exe (нужны для слияния видео+аудио)
│
└── app/                   ← Tauri приложение
    ├── src/               ← Frontend (HTML/CSS/JS)
    │   ├── index.html
    │   ├── style.css
    │   └── main.js
    │
    ├── src-tauri/         ← Backend (Rust)
    │   ├── src/main.rs
    │   ├── Cargo.toml
    │   └── tauri.conf.json
    │
    ├── ffmpeg/bin/        ← ffmpeg для Tauri сборки
    └── docs/              ← Документация
```

## Возможности

- Загрузка видео от 144p до 4K
- Извлечение аудио в MP3 320 kbps
- Прогресс-бар в реальном времени
- Выбор папки сохранения
- Автоматическое слияние видео+аудио через ffmpeg
- Graceful fallback без ffmpeg (видео без звука)

## Требования

- **Python 3.10+** (для актуальных версий yt-dlp)
- **Rust** (только для сборки Tauri-версии)
- **ffmpeg** — нужен для объединения отдельных видео- и аудиопотоков и конвертации в MP3; скачивается через `download_ffmpeg.bat`

## ffmpeg

Для слияния видео и аудио потоков необходим ffmpeg. Бинарник уже включён в `ffmpeg/bin/`. Если его нет — запустите:

```bash
download_ffmpeg.bat
```

Или скачайте вручную: https://www.gyan.dev/ffmpeg/builds/ → `ffmpeg-release-essentials.zip` → скопируйте `ffmpeg.exe` в `ffmpeg/bin/`.

## Лицензия

MIT License
