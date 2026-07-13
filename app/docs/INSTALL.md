# 📥 Инструкция по установке зависимостей

## Шаг 1: Установка Python

### Windows

1. Перейдите на https://python.org/downloads/
2. Скачайте последнюю версию Python (3.11+)
3. Запустите установщик
4. **ВАЖНО:** Отметьте галочку "Add Python to PATH"
5. Нажмите "Install Now"

### Проверка установки

Откройте командную строку (cmd) и выполните:
```bash
python --version
```

Должно вывести: `Python 3.11.x` или выше

---

## Шаг 2: Установка Rust

### Windows

1. Перейдите на https://rustup.rs
2. Скачайте `rustup-init.exe`
3. Запустите файл
4. Следуйте инструкциям (нажмите Enter для выбора по умолчанию)
5. После установки перезапустите командную строку

### Проверка установки

```bash
rustc --version
```

Должно вывести: `rustc 1.70.0` или выше

---

## Шаг 3: Установка WebView2 (если необходимо)

WebView2 обычно уже установлен в Windows 10/11.

### Проверка

1. Откройте "Параметры" → "Приложения"
2. Найдите "Microsoft Edge WebView2 Runtime"

### Если не установлен

1. Перейдите на https://developer.microsoft.com/en-us/microsoft-edge/webview2/
2. Скачайте "Evergreen Bootstrapper"
3. Запустите установщик

---

## Шаг 4: Установка Visual Studio Build Tools (для Rust)

### Windows

1. Перейдите на https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Скачайте "Build Tools for Visual Studio 2022"
3. Запустите установщик
4. Выберите "Разработка классических приложений на C++"
5. Убедитесь, что выбраны:
   - MSVC v143 build tools
   - Windows 10/11 SDK
6. Нажмите "Установить"

---

## Шаг 5: Установка Node.js (опционально)

Node.js не обязателен, но может понадобиться для некоторых Tauri функций.

### Windows

1. Перейдите на https://nodejs.org/
2. Скачайте LTS версию
3. Запустите установщик
4. Используйте настройки по умолчанию

### Проверка

```bash
node --version
npm --version
```

---

## Шаг 6: Установка Python зависимостей

Откройте командную строку в папке проекта:

```bash
cd C:\Users\Smixr\Desktop\Downloader
pip install yt-dlp
```

---

## Шаг 7: Установка Tauri CLI

```bash
cargo install tauri-cli --version "^1.6"
```

Это может занять несколько минут.

---

## Шаг 8: Запуск приложения

### Режим разработки

```bash
dev.bat
```

### Сборка EXE

```bash
build.bat
```

---

## 🔧 Решение проблем

### Ошибка: "python is not recognized"

**Решение:**
1. Переустановите Python
2. Обязательно отметьте "Add Python to PATH"
3. Или добавьте Python в PATH вручную:
   - "Параметры" → "Система" → "О системе" → "Дополнительные параметры системы"
   - "Переменные среды" → "Path" → "Изменить"
   - Добавьте: `C:\Users\ВашеИмя\AppData\Local\Programs\Python\Python311\Scripts\`
   - Добавьте: `C:\Users\ВашеИмя\AppData\Local\Programs\Python\Python311\`

### Ошибка: "rustc is not recognized"

**Решение:**
1. Перезапустите командную строку
2. Если не помогло, добавьте Rust в PATH:
   - Добавьте: `C:\Users\ВашеИмя\.cargo\bin\`

### Ошибка: "linker 'link.exe' not found"

**Решение:**
1. Установите Visual Studio Build Tools
2. Выберите "Разработка классических приложений на C++"

### Ошибка: "WebView2 not found"

**Решение:**
1. Установите WebView2 Runtime
2. Скачайте с https://developer.microsoft.com/en-us/microsoft-edge/webview2/

### Ошибка сборки Tauri

**Решение:**
```bash
# Очистите кэш
cd src-tauri
cargo clean

# Обновите зависимости
cargo update

# Пересоберите
cargo tauri build
```

### Ошибка: "failed to download FFmpeg"

**Решение:**
1. Скачайте FFmpeg вручную:
   - https://github.com/BtbN/FFmpeg-Builds/releases
   - Выберите "ffmpeg-master-latest-win64-gpl.zip"
2. Распакуйте в папку `ffmpeg\`
3. Убедитесь, что `ffmpeg.exe` находится в `ffmpeg\bin\`

---

## 📋 Чек-лист установки

- [ ] Python 3.8+ установлен
- [ ] Python добавлен в PATH
- [ ] Rust установлен
- [ ] Rust добавлен в PATH
- [ ] Visual Studio Build Tools установлен
- [ ] WebView2 Runtime установлен
- [ ] Node.js установлен (опционально)
- [ ] yt-dlp установлен (`pip install yt-dlp`)
- [ ] Tauri CLI установлен (`cargo install tauri-cli`)
- [ ] FFmpeg скачан (опционально, скачивается автоматически)

---

## 🚀 Быстрая установка (все команды)

```bash
# 1. Установите Python зависимости
pip install yt-dlp

# 2. Установите Tauri CLI
cargo install tauri-cli --version "^1.6"

# 3. Запустите сборку
build.bat
```

---

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте все зависимости установлены
2. Перезапустите командную строку
3. Проверьте PATH
4. Попробуйте переустановить проблемный компонент

---

**Удачи в сборке! 🎉**
