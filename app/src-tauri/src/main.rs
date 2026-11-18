#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use std::process::{Command, Stdio};
use std::io::{BufRead, BufReader};
use std::thread;
use std::sync::{Mutex, atomic::{AtomicBool, Ordering}};
use std::time::Duration;
use tauri::{Manager, Window};

struct DownloadState {
    active_child: Mutex<Option<std::process::Child>>,
    cancel_requested: AtomicBool,
}

#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;

#[cfg(target_os = "windows")]
const CREATE_NO_WINDOW: u32 = 0x08000000;

// Команда для получения информации о видео
#[tauri::command]
fn get_video_info(window: Window, url: String) -> Result<String, String> {
    let python_script = r#"
import sys
import json
import yt_dlp

def normalize_youtube_url(value):
    from urllib.parse import urlsplit, parse_qs
    import re
    if not isinstance(value,str) or not value.strip(): raise ValueError('URL is empty')
    value=value.strip()
    if value.startswith('//'): raise ValueError('Invalid YouTube URL')
    parsed=urlsplit(value if '://' in value else 'https://'+value)
    if parsed.scheme.lower() not in ('http','https'): raise ValueError('Only HTTP and HTTPS URLs are allowed')
    host=(parsed.hostname or '').lower().rstrip('.')
    allowed={'youtube.com','www.youtube.com','m.youtube.com','music.youtube.com','youtu.be','www.youtu.be'}
    if host not in allowed or parsed.username or parsed.password: raise ValueError('Only valid YouTube URLs are allowed')
    if parsed.port is not None and parsed.port not in (80,443): raise ValueError('Unsupported URL port')
    if host.endswith('youtu.be'): video_id=parsed.path.strip('/').split('/')[0]
    elif parsed.path=='/watch': video_id=parse_qs(parsed.query).get('v',[''])[0]
    else:
        parts=[p for p in parsed.path.split('/') if p]
        video_id=parts[1] if len(parts)==2 and parts[0] in ('embed','shorts','live','v') else ''
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}',video_id): raise ValueError('Invalid YouTube video URL')
    return value if '://' in value else 'https://'+value

# Принудительно устанавливаем UTF-8 кодировку для stdout
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

def get_info(url):
    url = normalize_youtube_url(url)
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Получаем доступные форматы
            formats = []
            if 'formats' in info:
                for f in info['formats']:
                    if f.get('vcodec') != 'none' and f.get('height') is not None:
                        format_info = {
                            'format_id': f.get('format_id'),
                            'height': f.get('height'),
                            'ext': f.get('ext'),
                            'filesize': f.get('filesize') or f.get('filesize_approx'),
                            'fps': f.get('fps'),
                            'vcodec': f.get('vcodec'),
                            'acodec': f.get('acodec'),
                        }
                        formats.append(format_info)
            
            # Сортируем по высоте
            formats.sort(key=lambda x: x['height'] if x['height'] else 0)
            
            # Убираем дубликаты по высоте
            seen_heights = set()
            unique_formats = []
            for f in formats:
                h = f['height']
                if h not in seen_heights:
                    seen_heights.add(h)
                    unique_formats.append(f)
            
            result = {
                'title': info.get('title', 'Unknown'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Unknown'),
                'view_count': info.get('view_count', 0),
                'formats': unique_formats
            }
            
            print(json.dumps(result, ensure_ascii=False))
            return 0
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False))
        return 1

if __name__ == '__main__':
    url = sys.argv[1]
    sys.exit(get_info(url))
"#;

    // Записываем скрипт во временный файл
    let temp_script = std::env::temp_dir().join(format!("yt_info_{}_{}.py", std::process::id(), std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap_or_default().as_nanos()));
    std::fs::write(&temp_script, python_script).map_err(|e| e.to_string())?;

    // Запускаем Python скрипт с скрытым окном и UTF-8 кодировкой
    let mut cmd = Command::new("python");
    cmd.arg(temp_script.to_str().unwrap())
        .arg(&url)
        .env("PYTHONIOENCODING", "utf-8")
        .env("PYTHONUTF8", "1")
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    
    #[cfg(target_os = "windows")]
    cmd.creation_flags(CREATE_NO_WINDOW);
    
    let output = cmd.output()
        .map_err(|e| format!("Failed to execute Python: {}", e))?;

    // Декодируем вывод как UTF-8
    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();

    if !stderr.is_empty() && output.status.code() != Some(0) {
        return Err(format!("Python error: {}", stderr));
    }

    // Удаляем временный файл
    let _ = std::fs::remove_file(temp_script);

    Ok(stdout.trim().to_string())
}

// Команда для начала загрузки
#[tauri::command]
fn start_download(
    window: Window,
    state: tauri::State<'_, DownloadState>,
    url: String,
    quality: String,
    format_type: String,
    save_path: String,
) -> Result<String, String> {
    // Находим путь к ffmpeg относительно исполняемого файла
    let exe_dir = std::env::current_exe()
        .ok()
        .and_then(|p| p.parent().map(|p| p.to_path_buf()))
        .unwrap_or_else(|| std::env::current_dir().unwrap_or_default());
    let requested_save_path = std::path::PathBuf::from(&save_path);
    let save_path = if requested_save_path.is_absolute() {
        requested_save_path
    } else {
        exe_dir.join(requested_save_path)
    };
    let save_path = save_path.to_string_lossy().to_string();

    // Проверяем несколько возможных расположений ffmpeg
    let ffmpeg_paths = [
        exe_dir.join("ffmpeg").join("bin").join("ffmpeg.exe"),
        exe_dir.join("ffmpeg").join("ffmpeg.exe"),
        exe_dir.join("app").join("ffmpeg").join("bin").join("ffmpeg.exe"),
        std::path::PathBuf::from(r"C:\ffmpeg\bin\ffmpeg.exe"),
    ];
    
    // yt-dlp требует ДИРЕКТОРИЮ, а не путь к файлу
    let ffmpeg_location = ffmpeg_paths.iter()
        .find(|p| p.exists())
        .and_then(|p| p.parent())
        .map(|p| p.to_string_lossy().to_string())
        .unwrap_or_default();
    
    let python_script = r#"
import sys
import json
import os
import yt_dlp

def normalize_youtube_url(value):
    from urllib.parse import urlsplit, parse_qs
    import re
    if not isinstance(value,str) or not value.strip(): raise ValueError('URL is empty')
    value=value.strip()
    if value.startswith('//'): raise ValueError('Invalid YouTube URL')
    parsed=urlsplit(value if '://' in value else 'https://'+value)
    if parsed.scheme.lower() not in ('http','https'): raise ValueError('Only HTTP and HTTPS URLs are allowed')
    host=(parsed.hostname or '').lower().rstrip('.')
    allowed={'youtube.com','www.youtube.com','m.youtube.com','music.youtube.com','youtu.be','www.youtu.be'}
    if host not in allowed or parsed.username or parsed.password: raise ValueError('Only valid YouTube URLs are allowed')
    if parsed.port is not None and parsed.port not in (80,443): raise ValueError('Unsupported URL port')
    if host.endswith('youtu.be'): video_id=parsed.path.strip('/').split('/')[0]
    elif parsed.path=='/watch': video_id=parse_qs(parsed.query).get('v',[''])[0]
    else:
        parts=[p for p in parsed.path.split('/') if p]
        video_id=parts[1] if len(parts)==2 and parts[0] in ('embed','shorts','live','v') else ''
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}',video_id): raise ValueError('Invalid YouTube video URL')
    return value if '://' in value else 'https://'+value

# Принудительно устанавливаем UTF-8 кодировку для stdout
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

def find_ffmpeg(ffmpeg_arg=None):
    # Сначала проверяем путь, переданный из Rust (это ДИРЕКТОРИЯ)
    if ffmpeg_arg and os.path.isdir(ffmpeg_arg):
        candidate = os.path.join(ffmpeg_arg, 'ffmpeg.exe')
        if os.path.exists(candidate):
            return ffmpeg_arg  # возвращаем директорию
        # Может быть передан полный путь к файлу
    if ffmpeg_arg and os.path.isfile(ffmpeg_arg):
        return os.path.dirname(ffmpeg_arg)  # возвращаем директорию
    
    possible_dirs = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ffmpeg', 'bin'),
        os.path.join(os.path.dirname(sys.executable), 'ffmpeg', 'bin'),
        os.path.join(os.getcwd(), 'ffmpeg', 'bin'),
        os.path.join(os.getcwd(), 'app', 'ffmpeg', 'bin'),
        os.path.join(os.getcwd(), 'ffmpeg'),
        os.path.dirname(sys.executable),
        r'C:\ffmpeg\bin',
    ]
    
    for d in possible_dirs:
        if os.path.exists(os.path.join(d, 'ffmpeg.exe')):
            return d
    
    # Проверяем PATH
    import shutil
    ffmpeg_in_path = shutil.which('ffmpeg')
    if ffmpeg_in_path:
        return os.path.dirname(ffmpeg_in_path)
    
    return None

def progress_hook(d):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        downloaded = d.get('downloaded_bytes', 0)
        progress = (downloaded / total * 100) if total > 0 else 0
        speed = d.get('speed', 0) or 0
        eta = d.get('eta', 0) or 0
        
        data = {
            'type': 'progress',
            'progress': round(progress, 2),
            'speed': speed,
            'eta': eta,
            'downloaded': downloaded,
            'total': total
        }
        print(json.dumps(data, ensure_ascii=False), flush=True)
    
    elif d['status'] == 'finished':
        data = {'type': 'finished', 'filename': d.get('filename', '')}
        print(json.dumps(data, ensure_ascii=False), flush=True)

def download(url, quality, format_type, save_path, ffmpeg_arg=None):
    url = normalize_youtube_url(url)
    save_path = os.path.abspath(os.path.expanduser(save_path))
    os.makedirs(save_path, exist_ok=True)
    ffmpeg_dir = find_ffmpeg(ffmpeg_arg)
    has_ffmpeg = ffmpeg_dir is not None and os.path.exists(os.path.join(ffmpeg_dir, 'ffmpeg.exe'))
    
    # Определяем формат
    if format_type == 'audio':
        format_string = 'bestaudio/best'
    elif quality == 'best':
        if has_ffmpeg:
            format_string = 'bestvideo+bestaudio/best'
        else:
            format_string = 'best'
    else:
        height = int(quality.replace('p', ''))
        if has_ffmpeg:
            format_string = f'bestvideo[height<={height}]+bestaudio[ext=m4a]/bestvideo[height<={height}]+bestaudio/best'
        else:
            format_string = f'best[height<={height}]/best'
    
    # Шаблон имени файла
    output_template = os.path.join(save_path, '%(title)s.%(ext)s')
    
    ydl_opts = {
        'format': format_string,
        'outtmpl': output_template,
        'progress_hooks': [progress_hook],
    }
    
    if has_ffmpeg:
        ydl_opts['ffmpeg_location'] = ffmpeg_dir
        ydl_opts['merge_output_format'] = 'mp4'
    
    if format_type == 'audio':
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }]
    elif has_ffmpeg:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }]
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if format_type == 'audio':
                filename = os.path.splitext(filename)[0] + '.mp3'
            
            result = {
                'type': 'complete',
                'success': True,
                'filename': filename,
                'title': info.get('title', 'Unknown')
            }
            print(json.dumps(result, ensure_ascii=False), flush=True)
            return 0
    except Exception as e:
        result = {
            'type': 'error',
            'success': False,
            'error': str(e)
        }
        print(json.dumps(result, ensure_ascii=False), flush=True)
        return 1

if __name__ == '__main__':
    url = sys.argv[1]
    quality = sys.argv[2]
    format_type = sys.argv[3]
    save_path = sys.argv[4]
    ffmpeg_arg = sys.argv[5] if len(sys.argv) > 5 else None
    sys.exit(download(url, quality, format_type, save_path, ffmpeg_arg))
"#;

    // Записываем скрипт во временный файл
    let temp_script = std::env::temp_dir().join(format!("yt_download_{}_{}.py", std::process::id(), std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap_or_default().as_nanos()));
    std::fs::write(&temp_script, python_script).map_err(|e| e.to_string())?;

    // Запускаем Python скрипт с выводом в реальном времени и скрытым окном
    let mut cmd = Command::new("python");
    cmd.arg(temp_script.to_str().unwrap())
        .arg(&url)
        .arg(&quality)
        .arg(&format_type)
        .arg(&save_path)
        .arg(&ffmpeg_location)
        .env("PYTHONIOENCODING", "utf-8")
        .env("PYTHONUTF8", "1")
        .env("PATH", format!("{};{}", ffmpeg_location, std::env::var("PATH").unwrap_or_default()))
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    
    #[cfg(target_os = "windows")]
    cmd.creation_flags(CREATE_NO_WINDOW);
    
    let mut child = cmd.spawn()
        .map_err(|e| {
            let _ = std::fs::remove_file(&temp_script);
            format!("Failed to start Python: {}", e)
        })?;

    {
        let mut active = state.active_child.lock().map_err(|e| e.to_string())?;
        if active.is_some() {
            let _ = child.kill();
            let _ = std::fs::remove_file(&temp_script);
            return Err("A download is already running".to_string());
        }
        state.cancel_requested.store(false, Ordering::SeqCst);
        *active = Some(child);
    }

    // Читаем вывод в реальном времени
    if let Some(stdout) = child.stdout.take() {
        let reader = BufReader::new(stdout);
        let window_clone = window.clone();
        
        thread::spawn(move || {
            for line in reader.lines() {
                if let Ok(line) = line {
                    // Отправляем прогресс в frontend
                    let _ = window_clone.emit("download-progress", &line);
                }
            }
        });
    }

    // Drain stderr concurrently to prevent a full pipe from blocking the child.
    if let Some(stderr) = child.stderr.take() {
        thread::spawn(move || {
            for line in BufReader::new(stderr).lines() {
                if let Ok(line) = line { eprintln!("[yt-dlp] {}", line); }
            }
        });
    }

    // Poll without holding the mutex while sleeping so cancel_download can kill the child.
    let status = loop {
        let mut active = state.active_child.lock().map_err(|e| e.to_string())?;
        let child = active.as_mut().ok_or_else(|| "Download process is unavailable".to_string())?;
        match child.try_wait() {
            Ok(Some(status)) => {
                active.take();
                break status;
            }
            Ok(None) => {}
            Err(error) => {
                if let Some(mut child) = active.take() {
                    let _ = child.kill();
                }
                let _ = std::fs::remove_file(&temp_script);
                return Err(format!("Failed waiting for Python downloader: {}", error));
            }
        }
        drop(active);
        thread::sleep(Duration::from_millis(100));
    };

    let was_cancelled = state.cancel_requested.swap(false, Ordering::SeqCst);
    let _ = std::fs::remove_file(temp_script);

    if was_cancelled {
        Ok("Download cancelled".to_string())
    } else if status.success() {
        Ok("Download completed".to_string())
    } else {
        Err("Download failed. Check the application log for yt-dlp details.".to_string())
    }
}

// Команда для отмены загрузки
#[tauri::command]
fn cancel_download(state: tauri::State<'_, DownloadState>) -> Result<String, String> {
    let mut active = state.active_child.lock().map_err(|e| e.to_string())?;
    match active.as_mut() {
        Some(child) => {
            state.cancel_requested.store(true, Ordering::SeqCst);
            child.kill().map_err(|e| format!("Failed to cancel download: {}", e))?;
            Ok("Cancellation requested".to_string())
        }
        None => Err("No active download".to_string()),
    }
}

// Команда для выбора папки сохранения
#[tauri::command]
async fn select_folder(window: Window) -> Result<String, String> {
    use tauri::api::dialog::blocking::FileDialogBuilder;
    
    let folder = FileDialogBuilder::new()
        .set_title("Select download folder")
        .pick_folder();
    
    match folder {
        Some(path) => Ok(path.to_string_lossy().to_string()),
        None => Err("No folder selected".to_string()),
    }
}

fn main() {
    tauri::Builder::default()
        .manage(DownloadState {
            active_child: Mutex::new(None),
            cancel_requested: AtomicBool::new(false),
        })
        .invoke_handler(tauri::generate_handler![
            get_video_info,
            start_download,
            cancel_download,
            select_folder,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
