# YouTube Downloader — Tauri + Python

Проект содержит две рабочие точки запуска:

- **Tauri GUI:** HTML/CSS/JavaScript в `app/src`, Rust-команды и запуск yt-dlp в `app/src-tauri`.
- **Standalone Python GUI:** `downloader.py` с CustomTkinter.

## Возможности

- Загрузка видео YouTube с выбором качества.
- Извлечение аудио в MP3 при наличии FFmpeg.
- Прогресс загрузки и отмена.
- Выбор папки сохранения.
- Проверка и нормализация ссылок YouTube.

## Требования

- Python 3.10+ и `yt-dlp`.
- Для standalone GUI также устанавливается CustomTkinter из корневого `requirements.txt`.
- Для Tauri-разработки и сборки: Rust, Tauri CLI 1.x, WebView2 и Windows C++ Build Tools.
- FFmpeg необязателен для базовой загрузки, но нужен для объединения потоков и MP3-конвертации.

## Быстрый старт

Из корня репозитория:

```bat
python -m pip install -r requirements.txt
run.bat
```

Для разработки Tauri:

```bat
dev.bat
```

Для сборки Tauri EXE:

```bat
build.bat
```

EXE создаётся в корне репозитория как `YouTube Downloader.exe`.

**Ограничение упаковки:** текущий Tauri EXE запускает системный Python и требует установленный `yt-dlp`; он не включает в себя интерпретатор Python и все Python-зависимости. Для FFmpeg можно использовать `download_ffmpeg.bat`.

## Фактическая структура

```text
Downloader/
├── downloader.py
├── url_utils.py
├── config.json
├── requirements.txt
├── run.bat
├── build.bat
├── dev.bat
├── download_ffmpeg.bat
├── Downloader.spec
├── tests/
├── .github/workflows/ci.yml
└── app/
    ├── src/
    │   ├── index.html
    │   ├── style.css
    │   └── main.js
    ├── src-tauri/
    │   ├── src/main.rs
    │   ├── Cargo.toml
    │   └── tauri.conf.json
    ├── backend/requirements.txt
    └── docs/
```

Дополнительные сведения по установке — в `INSTALL.md`; подробная карта файлов — в `STRUCTURE.md`.
