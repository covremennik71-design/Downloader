"""
YouTube Video Downloader
========================
Простой загрузчик видео с YouTube с графическим интерфейсом.
Поддерживает выбор качества видео (от 144p до 2160p/4K).

Для использования YouTube Data API (поиск видео) укажите ключ в config.json
или через настройки в приложении.
"""

import os
import sys
import json
import threading
import re
import shutil
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
from datetime import timedelta
from url_utils import normalize_youtube_url

# Путь к конфигу
def get_base_dir():
    """Получить базовую директорию (для exe и скрипта)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")

# Создаём папку загрузок
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# ==================== ПОИСК FFMPEG ====================
def find_ffmpeg():
    """
    Ищет ffmpeg в нескольких местах:
    1. PyInstaller _MEIPASS (для EXE)
    2. Локальная папка ffmpeg/bin/ рядом с программой
    3. Системный PATH
    4. Стандартные места установки
    Возвращает путь к ffmpeg.exe или None.
    """
    # 1. PyInstaller temp directory (для EXE)
    if getattr(sys, 'frozen', False):
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            meipass_paths = [
                os.path.join(meipass, "ffmpeg", "bin", "ffmpeg.exe"),
                os.path.join(meipass, "ffmpeg", "ffmpeg.exe"),
                os.path.join(meipass, "ffmpeg.exe"),
            ]
            for path in meipass_paths:
                if os.path.exists(path):
                    print(f"[FFMPEG] Found in MEIPASS: {path}")
                    return path
    
    # 2. Локальная папка рядом с exe/скриптом
    local_paths = [
        os.path.join(BASE_DIR, "ffmpeg", "bin", "ffmpeg.exe"),
        os.path.join(BASE_DIR, "ffmpeg", "ffmpeg.exe"),
        os.path.join(BASE_DIR, "ffmpeg.exe"),
        os.path.join(BASE_DIR, "tools", "ffmpeg", "bin", "ffmpeg.exe"),
    ]
    
    for path in local_paths:
        if os.path.exists(path):
            print(f"[FFMPEG] Found locally: {path}")
            return path
    
    # 3. Проверяем системный PATH
    ffmpeg_in_path = shutil.which("ffmpeg")
    if ffmpeg_in_path:
        print(f"[FFMPEG] Found in PATH: {ffmpeg_in_path}")
        return ffmpeg_in_path
    
    # 4. Стандартные места установки на Windows
    common_paths = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
        os.path.expanduser(r"~\ffmpeg\bin\ffmpeg.exe"),
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            print(f"[FFMPEG] Found in common path: {path}")
            return path
    
    print("[FFMPEG] WARNING: ffmpeg.exe not found!")
    return None

FFMPEG_PATH = find_ffmpeg()

# ==================== КОНФИГУРАЦИЯ ====================
DEFAULT_CONFIG = {
    "youtube_api_key": "",
    "download_path": DOWNLOADS_DIR,
    "theme": "dark",
    "video_format": "mp4",
    "audio_format": "mp3",
    "default_quality": "1080p",
}

def load_config():
    """Загрузить конфигурацию из файла."""
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            print(f"Ошибка загрузки конфига: {e}")
    else:
        save_config(config)

    configured_path = config.get("download_path") or DOWNLOADS_DIR
    if not os.path.isabs(configured_path):
        configured_path = os.path.join(BASE_DIR, configured_path)
    config["download_path"] = os.path.normpath(configured_path)
    return config

def save_config(config):
    """Сохранить конфигурацию в файл."""
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Ошибка сохранения конфига: {e}")

# ==================== ЗАГРУЗЧИК ====================
class YouTubeDownloader:
    """Класс для скачивания видео с YouTube."""
    
    def __init__(self, config):
        self.config = config
        self.is_downloading = False
        self.cancel_flag = False
    
    def get_video_info(self, url):
        """Получить информацию о видео."""
        url = normalize_youtube_url(url)
        import yt_dlp
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'uploader': info.get('uploader', 'Unknown'),
                    'description': info.get('description', '')[:200],
                    'formats': info.get('formats', []),
                }
        except Exception as e:
            raise Exception(f"Не удалось получить информацию: {e}")
    
    def get_available_qualities(self, info):
        """Получить список доступных качеств."""
        qualities = set()
        formats = info.get('formats', [])
        
        for f in formats:
            height = f.get('height')
            if height and f.get('vcodec') != 'none':
                if height <= 144:
                    qualities.add('144p')
                elif height <= 240:
                    qualities.add('240p')
                elif height <= 360:
                    qualities.add('360p')
                elif height <= 480:
                    qualities.add('480p')
                elif height <= 720:
                    qualities.add('720p')
                elif height <= 1080:
                    qualities.add('1080p')
                elif height <= 1440:
                    qualities.add('1440p (2K)')
                elif height <= 2160:
                    qualities.add('2160p (4K)')
                else:
                    qualities.add(f'{height}p')
        
        # Сортировка по возрастанию
        quality_order = ['144p', '240p', '360p', '480p', '720p', '1080p', 
                        '1440p (2K)', '2160p (4K)']
        
        result = []
        for q in quality_order:
            if q in qualities:
                result.append(q)
        
        # Добавляем нестандартные
        for q in sorted(qualities):
            if q not in result:
                result.append(q)
        
        result.append('Лучшее качество')
        result.append('Только аудио (MP3)')
        
        return result
    
    def format_selector(self, quality, has_ffmpeg=True):
        """Вернуть формат для yt-dlp в зависимости от выбранного качества."""
        if not has_ffmpeg:
            # Без ffmpeg нельзя сливать видео+аудио, используем одиночный поток
            quality_map = {
                '144p': 'best[height<=144]/best',
                '240p': 'best[height<=240]/best',
                '360p': 'best[height<=360]/best',
                '480p': 'best[height<=480]/best',
                '720p': 'best[height<=720]/best',
                '1080p': 'best[height<=1080]/best',
                '1440p (2K)': 'best[height<=1440]/best',
                '2160p (4K)': 'best[height<=2160]/best',
                'Лучшее качество': 'best',
                'Только аудио (MP3)': 'bestaudio/best',
            }
            return quality_map.get(quality, 'best')
        
        quality_map = {
            '144p': 'bestvideo[height<=144]+bestaudio[ext=m4a]/bestvideo[height<=144]+bestaudio/best[height<=144]/best',
            '240p': 'bestvideo[height<=240]+bestaudio[ext=m4a]/bestvideo[height<=240]+bestaudio/best[height<=240]/best',
            '360p': 'bestvideo[height<=360]+bestaudio[ext=m4a]/bestvideo[height<=360]+bestaudio/best[height<=360]/best',
            '480p': 'bestvideo[height<=480]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best[height<=480]/best',
            '720p': 'bestvideo[height<=720]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]/best',
            '1080p': 'bestvideo[height<=1080]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
            '1440p (2K)': 'bestvideo[height<=1440]+bestaudio[ext=m4a]/bestvideo[height<=1440]+bestaudio/best[height<=1440]/best',
            '2160p (4K)': 'bestvideo[height<=2160]+bestaudio[ext=m4a]/bestvideo[height<=2160]+bestaudio/best[height<=2160]/best',
            'Лучшее качество': 'bestvideo+bestaudio[ext=m4a]/bestvideo+bestaudio/best',
            'Только аудио (MP3)': 'bestaudio/best',
        }
        return quality_map.get(quality, 'bestvideo+bestaudio/best')
    
    def download(self, url, quality, save_path, progress_callback=None, 
                 info_callback=None, error_callback=None, complete_callback=None):
        """Скачать видео."""
        url = normalize_youtube_url(url)
        save_path = os.path.abspath(os.path.expanduser(save_path))
        os.makedirs(save_path, exist_ok=True)
        import yt_dlp
        
        self.is_downloading = True
        self.cancel_flag = False
        
        def progress_hook(d):
            if self.cancel_flag:
                raise Exception("Загрузка отменена")
            
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                speed = d.get('speed', 0)
                eta = d.get('eta', 0)
                
                if total > 0:
                    percent = (downloaded / total) * 100
                else:
                    percent = 0
                
                if progress_callback:
                    progress_callback(percent, speed, eta)
            
            elif d['status'] == 'finished':
                if progress_callback:
                    progress_callback(100, 0, 0)
        
        try:
            # Определение формата
            ffmpeg_path = find_ffmpeg()
            has_ffmpeg = ffmpeg_path is not None
            format_str = self.format_selector(quality, has_ffmpeg)
            is_audio_only = quality == 'Только аудио (MP3)'
            
            # Шаблон имени файла
            outtmpl = os.path.join(save_path, '%(title)s.%(ext)s')
            
            # === КЛЮЧЕВОЕ: Указываем путь к ffmpeg для слияния видео+аудио ===
            
            ydl_opts = {
                'format': format_str,
                'outtmpl': outtmpl,
                'progress_hooks': [progress_hook],
                'quiet': False,
                'no_warnings': False,
                'postprocessor_args': [],
            }
            
            # Указываем ffmpeg_location (путь к директории с ffmpeg.exe)
            if has_ffmpeg:
                ffmpeg_dir = os.path.dirname(ffmpeg_path)
                ydl_opts['ffmpeg_location'] = ffmpeg_dir
                ydl_opts['merge_output_format'] = 'mp4'
                if info_callback:
                    info_callback(f"FFmpeg найден: {ffmpeg_path}")
            else:
                if info_callback:
                    info_callback("FFmpeg не найден! Скачивание в лучшем качестве без слияния.")
            
            # Если только аудио - конвертируем в MP3
            if is_audio_only:
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }]
                ydl_opts.pop('merge_output_format', None)
            elif has_ffmpeg:
                # Добавляем postprocessor для принудительного слияния видео+аудио
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }]
            
            # Удаляем None значения
            ydl_opts = {k: v for k, v in ydl_opts.items() if v is not None}
            
            if info_callback:
                info_callback("Получение информации о видео...")
            
            # Логируем настройки для отладки
            print(f"[YT-DLP] Format: {format_str}")
            print(f"[YT-DLP] FFmpeg location: {ydl_opts.get('ffmpeg_location', 'NOT SET')}")
            print(f"[YT-DLP] Merge format: {ydl_opts.get('merge_output_format', 'NOT SET')}")
            print(f"[YT-DLP] Postprocessors: {ydl_opts.get('postprocessors', [])}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'video')
                
                if info_callback:
                    info_callback(f"Скачивание: {title}")
                
                ydl.download([url])
                
                # Определяем путь к файлу
                filename = ydl.prepare_filename(info)
                if is_audio_only:
                    filename = os.path.splitext(filename)[0] + '.mp3'
                else:
                    filename = os.path.splitext(filename)[0] + '.mp4'
                
                # Проверяем, что файл существует
                if not os.path.exists(filename):
                    # Ищем файл с другим расширением
                    base = os.path.splitext(filename)[0]
                    for ext in ['.mp4', '.mkv', '.webm', '.m4a']:
                        test_file = base + ext
                        if os.path.exists(test_file):
                            filename = test_file
                            break
                
                if complete_callback:
                    complete_callback(filename, title)
                    
        except Exception as e:
            if error_callback:
                error_callback(str(e))
        finally:
            self.is_downloading = False
    
    def cancel(self):
        """Отменить загрузку."""
        self.cancel_flag = True


# ==================== GUI ====================
class DownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.config = load_config()
        self.downloader = YouTubeDownloader(self.config)
        self.current_info = None
        
        # Настройки окна
        self.title("YouTube Downloader")
        self.geometry("750x650")
        self.minsize(600, 500)
        
        # Тема
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Иконка
        icon_path = os.path.join(BASE_DIR, "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except:
                pass
        
        # Создаём интерфейс
        self.setup_ui()
        
        # Центрируем окно
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_ui(self):
        """Создать интерфейс."""
        # Главный контейнер
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # ===== Заголовок =====
        title_label = ctk.CTkLabel(
            main_frame,
            text="🎬 YouTube Downloader",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # ===== Поле для URL =====
        url_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        url_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(url_frame, text="Ссылка на видео:", 
                     font=ctk.CTkFont(size=13)).pack(anchor="w", pady=(0, 5))
        
        self.url_entry = ctk.CTkEntry(
            url_frame,
            height=40,
            placeholder_text="https://www.youtube.com/watch?v=...",
            font=ctk.CTkFont(size=13)
        )
        self.url_entry.pack(fill="x", pady=(0, 5))
        self.url_entry.bind("<KeyRelease>", self._invalidate_video_info)
        
        # ===== Информация о видео =====
        self.info_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        self.info_frame.pack(fill="x", pady=10)
        self.info_frame.pack_forget()  # Скрыто по умолчанию
        
        self.info_label = ctk.CTkLabel(
            self.info_frame,
            text="",
            font=ctk.CTkFont(size=12),
            wraplength=600
        )
        self.info_label.pack(padx=15, pady=10)
        
        # ===== Выбор качества =====
        quality_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        quality_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(quality_frame, text="Качество видео:", 
                     font=ctk.CTkFont(size=13)).pack(anchor="w", pady=(0, 5))
        
        self.quality_combo = ctk.CTkComboBox(
            quality_frame,
            values=["720p", "1080p", "Лучшее качество", "Только аудио (MP3)"],
            height=35,
            font=ctk.CTkFont(size=13),
            state="readonly"
        )
        self.quality_combo.set(self.config.get("default_quality", "720p"))
        self.quality_combo.pack(fill="x", pady=(0, 5))
        
        # ===== Папка сохранения =====
        path_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        path_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(path_frame, text="Папка сохранения:", 
                     font=ctk.CTkFont(size=13)).pack(anchor="w", pady=(0, 5))
        
        path_inner = ctk.CTkFrame(path_frame, fg_color="transparent")
        path_inner.pack(fill="x")
        
        self.path_entry = ctk.CTkEntry(
            path_inner,
            height=35,
            font=ctk.CTkFont(size=12)
        )
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.path_entry.insert(0, self.config.get("download_path", DOWNLOADS_DIR))
        
        self.browse_btn = ctk.CTkButton(
            path_inner,
            text="📁",
            width=40,
            height=35,
            command=self.browse_folder
        )
        self.browse_btn.pack(side="right")
        
        # ===== Кнопки управления =====
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=15)
        
        self.get_info_btn = ctk.CTkButton(
            btn_frame,
            text="🔍 Получить информацию",
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.get_info
        )
        self.get_info_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.download_btn = ctk.CTkButton(
            btn_frame,
            text="⬇️ Скачать",
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#28a745",
            hover_color="#218838",
            command=self.start_download
        )
        self.download_btn.pack(side="left", fill="x", expand=True, padx=(5, 5))
        
        self.cancel_btn = ctk.CTkButton(
            btn_frame,
            text="❌ Отмена",
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#dc3545",
            hover_color="#c82333",
            command=self.cancel_download,
            state="disabled"
        )
        self.cancel_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        # ===== Прогресс =====
        self.progress_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.progress_frame.pack(fill="x", pady=5)
        self.progress_frame.pack_forget()  # Скрыто по умолчанию
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=20)
        self.progress_bar.pack(fill="x", pady=(0, 5))
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.pack()
        
        # ===== Статус =====
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="Готов к работе",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.status_label.pack(pady=(10, 0))
        
        # ===== Нижняя панель =====
        bottom_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom_frame.pack(fill="x", side="bottom", pady=(10, 0))
        
        self.settings_btn = ctk.CTkButton(
            bottom_frame,
            text="⚙️ Настройки",
            width=120,
            height=32,
            font=ctk.CTkFont(size=12),
            fg_color="gray",
            hover_color="darkgray",
            command=self.open_settings
        )
        self.settings_btn.pack(side="right")
        
        self.api_label = ctk.CTkLabel(
            bottom_frame,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="orange"
        )
        self.api_label.pack(side="left")
        
        # Проверяем наличие API ключа
        self.check_api_key()
        
        # Проверяем наличие FFmpeg
        self.check_ffmpeg()
    
    def check_ffmpeg(self):
        """Проверить наличие FFmpeg."""
        ffmpeg = find_ffmpeg()
        if not ffmpeg:
            self.api_label.configure(
                text="⚠️ FFmpeg не найден! Видео будет без звука."
            )
        else:
            print(f"[APP] FFmpeg found: {ffmpeg}")
    
    def check_api_key(self):
        """Проверить наличие API ключа."""
        api_key = self.config.get("youtube_api_key", "")
        if not api_key or api_key == "ВСТАВЬТЕ_СЮДА_ВАШ_YOUTUBE_API_KEY":
            self.api_label.configure(
                text="⚠️ YouTube API ключ не указан (нажмите Настройки)"
            )
        else:
            self.api_label.configure(text="✅ YouTube API ключ настроен")
    
    def browse_folder(self):
        """Выбрать папку для сохранения."""
        folder = filedialog.askdirectory(
            title="Выберите папку для сохранения",
            initialdir=self.path_entry.get()
        )
        if folder:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder)
            self.config["download_path"] = folder
            save_config(self.config)
    
    def _invalidate_video_info(self, _event=None):
        """Сбросить метаданные, если пользователь изменил ссылку."""
        self.current_info = None

    def get_info(self):
        """Получить информацию о видео."""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Ошибка", "Введите ссылку на видео!")
            return
        
        try:
            url = normalize_youtube_url(url)
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, url)
        except ValueError as exc:
            messagebox.showwarning("Ошибка", str(exc))
            return
        self.current_info = None
        self.status_label.configure(text="Получение информации...", text_color="orange")
        self.get_info_btn.configure(state="disabled")
        
        thread = threading.Thread(target=self._get_info_thread, args=(url,))
        thread.daemon = True
        thread.start()
    
    def _get_info_thread(self, url):
        """Поток для получения информации."""
        try:
            info = self.downloader.get_video_info(url)
            # Build the UI payload in the worker, but update widgets only on Tk's main thread.
            qualities = self.downloader.get_available_qualities(info)
            
            # Показываем информацию
            duration = info.get('duration', 0)
            duration_str = str(timedelta(seconds=duration)) if duration else "N/A"
            
            info_text = (
                f"📹 {info.get('title', 'Unknown')}\n"
                f"👤 {info.get('uploader', 'Unknown')}\n"
                f"⏱️ Длительность: {duration_str}\n"
                f"🎬 Доступных качеств: {len([q for q in qualities if 'аудио' not in q and 'Лучшее' not in q])}"
            )
            
            self.after(0, lambda: self._show_info(info_text, info, qualities, url))
            
        except Exception as e:
            self.after(0, lambda: self._show_error(str(e)))
    
    def _apply_qualities(self, qualities):
        """Apply quality choices on the Tk main thread."""
        self.quality_combo.configure(values=qualities)
        if qualities:
            default = self.config.get("default_quality", "720p")
            if default in qualities:
                self.quality_combo.set(default)
            else:
                self.quality_combo.set(qualities[-3] if len(qualities) >= 3 else qualities[0])

    def _show_info(self, text, info, qualities, requested_url):
        """Показать информацию о видео на главном потоке Tk."""
        if self.url_entry.get().strip() != requested_url:
            self.get_info_btn.configure(state="normal")
            return
        self.current_info = info
        self._apply_qualities(qualities)
        self.info_label.configure(text=text)
        self.info_frame.pack(fill="x", pady=10)
        self.status_label.configure(text="Информация получена", text_color="green")
        self.get_info_btn.configure(state="normal")
    
    def _show_error(self, error):
        """Показать ошибку."""
        self.status_label.configure(text=f"Ошибка: {error[:100]}", text_color="red")
        self.get_info_btn.configure(state="normal")
        messagebox.showerror("Ошибка", f"Не удалось получить информацию:\n{error}")
    
    def start_download(self):
        """Начать загрузку - сначала получаем информацию и показываем выбор качества."""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Ошибка", "Введите ссылку на видео!")
            return
        
        if self.downloader.is_downloading:
            messagebox.showinfo("Информация", "Загрузка уже идёт!")
            return
        try:
            url = normalize_youtube_url(url)
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, url)
        except ValueError as exc:
            messagebox.showwarning("Ошибка", str(exc))
            return
        # Если метаданные ещё не получены — получаем их для нормализованного URL.
        if self.current_info is None:
            self.status_label.configure(text="Получение информации о видео...", text_color="orange")
            self.download_btn.configure(state="disabled")
            self.get_info_btn.configure(state="disabled")
            
            thread = threading.Thread(target=self._get_info_and_show_quality_dialog, args=(url,))
            thread.daemon = True
            thread.start()
        else:
            # Информация уже есть - показываем диалог выбора качества
            self.show_quality_selection_dialog()
    
    def _get_info_and_show_quality_dialog(self, url):
        """Получить информацию и показать диалог выбора качества."""
        try:
            info = self.downloader.get_video_info(url)
            # Keep all Tk widget access in the main-thread callback.
            qualities = self.downloader.get_available_qualities(info)
            
            # Показываем информацию в основном окне
            duration = info.get('duration', 0)
            duration_str = str(timedelta(seconds=duration)) if duration else "N/A"
            
            info_text = (
                f"📹 {info.get('title', 'Unknown')}\n"
                f"👤 {info.get('uploader', 'Unknown')}\n"
                f"⏱️ Длительность: {duration_str}\n"
                f"🎬 Доступных качеств: {len([q for q in qualities if 'аудио' not in q and 'Лучшее' not in q])}"
            )
            
            self.after(0, lambda: self._show_info_and_dialog(info_text, info, qualities, url))
            
        except Exception as e:
            self.after(0, lambda: self._show_error(str(e)))
    
    def _show_info_and_dialog(self, info_text, info, qualities, requested_url):
        """Показать информацию и диалог выбора качества на главном потоке Tk."""
        if self.url_entry.get().strip() != requested_url:
            self.download_btn.configure(state="normal")
            self.get_info_btn.configure(state="normal")
            return
        self.current_info = info
        self._apply_qualities(qualities)
        self.info_label.configure(text=info_text)
        self.info_frame.pack(fill="x", pady=10)
        self.status_label.configure(text="Информация получена", text_color="green")
        self.download_btn.configure(state="normal")
        self.get_info_btn.configure(state="normal")
        
        # Показываем диалог выбора качества
        self.show_quality_selection_dialog()
    
    def show_quality_selection_dialog(self):
        """Показать диалог выбора качества."""
        if self.current_info is None:
            return
        
        qualities = self.downloader.get_available_qualities(self.current_info)
        
        # Создаём диалог выбора качества
        dialog = ctk.CTkToplevel(self)
        dialog.title("Выберите качество")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        
        # Центрируем диалог
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - 200
        y = self.winfo_y() + (self.winfo_height() // 2) - 150
        dialog.geometry(f"+{x}+{y}")
        
        # Заголовок
        title_label = ctk.CTkLabel(
            dialog,
            text="🎬 Выберите качество для загрузки",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(20, 10))
        
        # Информация о видео
        info_text = f"📹 {self.current_info.get('title', 'Unknown')}"
        info_label = ctk.CTkLabel(
            dialog,
            text=info_text,
            font=ctk.CTkFont(size=12),
            wraplength=350
        )
        info_label.pack(pady=(0, 15))
        
        # Выпадающий список качеств
        quality_label = ctk.CTkLabel(
            dialog,
            text="Доступные качества:",
            font=ctk.CTkFont(size=13)
        )
        quality_label.pack(pady=(0, 5))
        
        quality_combo = ctk.CTkComboBox(
            dialog,
            values=qualities,
            height=35,
            width=300,
            font=ctk.CTkFont(size=13),
            state="readonly"
        )
        
        # Устанавливаем рекомендованное качество
        default = self.config.get("default_quality", "720p")
        if default in qualities:
            quality_combo.set(default)
        else:
            # Выбираем среднее качество
            video_qualities = [q for q in qualities if 'аудио' not in q and 'Лучшее' not in q]
            if video_qualities:
                mid_idx = len(video_qualities) // 2
                quality_combo.set(video_qualities[mid_idx])
            else:
                quality_combo.set(qualities[0])
        
        quality_combo.pack(pady=(0, 20))
        
        # Кнопки
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        def on_confirm():
            selected_quality = quality_combo.get()
            self.quality_combo.set(selected_quality)
            dialog.destroy()
            self._start_actual_download()
        
        def on_cancel():
            dialog.destroy()
            self.download_btn.configure(state="normal")
        
        ctk.CTkButton(
            btn_frame,
            text="✅ Скачать",
            height=35,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#28a745",
            hover_color="#218838",
            command=on_confirm
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ctk.CTkButton(
            btn_frame,
            text="❌ Отмена",
            height=35,
            font=ctk.CTkFont(size=13),
            fg_color="gray",
            hover_color="darkgray",
            command=on_cancel
        ).pack(side="left", fill="x", expand=True, padx=(5, 0))
    
    def _start_actual_download(self):
        """Начать фактическую загрузку после выбора качества."""
        url = self.url_entry.get().strip()
        quality = self.quality_combo.get()
        
        # Проверяем наличие FFmpeg
        ffmpeg = find_ffmpeg()
        if not ffmpeg and quality != 'Только аудио (MP3)':
            result = messagebox.askyesno(
                "FFmpeg не найден",
                "FFmpeg не найден! Видео будет скачано БЕЗ ЗВУКА.\n\n"
                "Продолжить загрузку?",
                icon=messagebox.WARNING
            )
            if not result:
                self.download_btn.configure(state="normal")
                return
        
        save_path = self.path_entry.get().strip()
        
        if not save_path or not os.path.exists(save_path):
            save_path = DOWNLOADS_DIR
            os.makedirs(save_path, exist_ok=True)
        
        # Сохраняем настройки
        self.config["default_quality"] = quality
        self.config["download_path"] = save_path
        save_config(self.config)
        
        # Блокируем кнопки
        self.download_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.get_info_btn.configure(state="disabled")
        
        # Показываем прогресс
        self.progress_frame.pack(fill="x", pady=5)
        self.progress_bar.set(0)
        self.progress_label.configure(text="Подготовка...")
        
        # Запускаем загрузку в потоке
        thread = threading.Thread(
            target=self.downloader.download,
            args=(url, quality, save_path),
            kwargs={
                'progress_callback': self.on_progress,
                'info_callback': self.on_info,
                'error_callback': self.on_error,
                'complete_callback': self.on_complete,
            }
        )
        thread.daemon = True
        thread.start()
    
    def on_progress(self, percent, speed, eta):
        """Обновить прогресс."""
        def update():
            self.progress_bar.set(percent / 100)
            
            speed_str = ""
            if speed:
                if speed > 1024 * 1024:
                    speed_str = f"{speed / (1024*1024):.1f} MB/s"
                else:
                    speed_str = f"{speed / 1024:.1f} KB/s"
            
            eta_str = ""
            if eta:
                eta_str = str(timedelta(seconds=eta))
            
            text = f"{percent:.1f}%"
            if speed_str:
                text += f" | {speed_str}"
            if eta_str:
                text += f" | Осталось: {eta_str}"
            
            self.progress_label.configure(text=text)
            self.status_label.configure(text=f"Загрузка... {percent:.0f}%", text_color="orange")
        
        self.after(0, update)
    
    def on_info(self, message):
        """Обновить информационное сообщение."""
        self.after(0, lambda: self.progress_label.configure(text=message))
        self.after(0, lambda: self.status_label.configure(text=message, text_color="orange"))
    
    def on_error(self, error):
        """Обработать ошибку."""
        def update():
            self.progress_frame.pack_forget()
            self.download_btn.configure(state="normal")
            self.cancel_btn.configure(state="disabled")
            self.get_info_btn.configure(state="normal")
            self.status_label.configure(text=f"Ошибка: {error[:100]}", text_color="red")
            messagebox.showerror("Ошибка загрузки", error)
        
        self.after(0, update)
    
    def on_complete(self, filepath, title):
        """Загрузка завершена."""
        def update():
            self.progress_bar.set(1)
            self.progress_label.configure(text="✅ Загрузка завершена!")
            self.progress_frame.pack(fill="x", pady=5)
            
            self.download_btn.configure(state="normal")
            self.cancel_btn.configure(state="disabled")
            self.get_info_btn.configure(state="normal")
            self.status_label.configure(text=f"✅ Сохранено: {os.path.basename(filepath)}", text_color="green")
            
            # Скрываем прогресс через 5 секунд
            self.after(5000, lambda: self.progress_frame.pack_forget())
            
            messagebox.showinfo("Готово", f"Видео скачано!\n\n{os.path.basename(filepath)}")
        
        self.after(0, update)
    
    def cancel_download(self):
        """Отменить загрузку."""
        self.downloader.cancel()
        self.status_label.configure(text="Отмена загрузки...", text_color="orange")
        self.cancel_btn.configure(state="disabled")
    
    def open_settings(self):
        """Открыть окно настроек."""
        SettingsWindow(self, self.config)


class SettingsWindow(ctk.CTkToplevel):
    """Окно настроек."""
    
    def __init__(self, parent, config):
        super().__init__(parent)
        
        self.config = config
        self.parent_app = parent
        
        self.title("Настройки")
        self.geometry("500x400")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui()
        
        # Центрируем
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 250
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 200
        self.geometry(f"+{x}+{y}")
    
    def setup_ui(self):
        """Создать интерфейс настроек."""
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # ===== YouTube API Key =====
        ctk.CTkLabel(
            main_frame,
            text="🔑 YouTube Data API Key",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        ctk.CTkLabel(
            main_frame,
            text="Ключ нужен для поиска видео. Получить: https://console.cloud.google.com/",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            wraplength=450
        ).pack(anchor="w", pady=(0, 5))
        
        self.api_entry = ctk.CTkEntry(
            main_frame,
            height=35,
            font=ctk.CTkFont(size=12),
            placeholder_text="AIzaSy..."
        )
        self.api_entry.pack(fill="x", pady=(0, 5))
        self.api_entry.insert(0, self.config.get("youtube_api_key", ""))
        
        # ===== Папка загрузок =====
        ctk.CTkLabel(
            main_frame,
            text="📁 Папка для загрузок по умолчанию",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(15, 5))
        
        path_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        path_frame.pack(fill="x")
        
        self.path_entry = ctk.CTkEntry(
            path_frame,
            height=35,
            font=ctk.CTkFont(size=12)
        )
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.path_entry.insert(0, self.config.get("download_path", DOWNLOADS_DIR))
        
        ctk.CTkButton(
            path_frame,
            text="📁",
            width=40,
            height=35,
            command=self.browse_path
        ).pack(side="right")
        
        # ===== Качество по умолчанию =====
        ctk.CTkLabel(
            main_frame,
            text="🎬 Качество по умолчанию",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(15, 5))
        
        self.quality_combo = ctk.CTkComboBox(
            main_frame,
            values=["360p", "480p", "720p", "1080p", "1440p (2K)", "2160p (4K)", 
                   "Лучшее качество", "Только аудио (MP3)"],
            height=35,
            font=ctk.CTkFont(size=12),
            state="readonly"
        )
        self.quality_combo.set(self.config.get("default_quality", "720p"))
        self.quality_combo.pack(fill="x", pady=(0, 5))
        
        # ===== Кнопки =====
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 0))
        
        ctk.CTkButton(
            btn_frame,
            text="💾 Сохранить",
            height=35,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.save_settings
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ctk.CTkButton(
            btn_frame,
            text="❌ Отмена",
            height=35,
            font=ctk.CTkFont(size=12),
            fg_color="gray",
            hover_color="darkgray",
            command=self.destroy
        ).pack(side="left", fill="x", expand=True, padx=(5, 0))
    
    def browse_path(self):
        """Выбрать папку."""
        folder = filedialog.askdirectory()
        if folder:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder)
    
    def save_settings(self):
        """Сохранить настройки."""
        self.config["youtube_api_key"] = self.api_entry.get().strip()
        self.config["download_path"] = self.path_entry.get().strip()
        self.config["default_quality"] = self.quality_combo.get()
        
        save_config(self.config)
        
        # Обновляем основное окно
        self.parent_app.path_entry.delete(0, tk.END)
        self.parent_app.path_entry.insert(0, self.config["download_path"])
        self.parent_app.check_api_key()
        
        messagebox.showinfo("Готово", "Настройки сохранены!")
        self.destroy()


# ==================== ЗАПУСК ====================
def main():
    """Запуск приложения."""
    app = DownloaderApp()
    app.mainloop()


if __name__ == "__main__":
    main()
