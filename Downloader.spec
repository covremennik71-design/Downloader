# -*- mode: python ; coding: utf-8 -*-
# Downloader.spec - Конфигурация PyInstaller для сборки EXE

import os
import sys
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Собираем данные для customtkinter
ctk_datas = []
try:
    ctk_datas = collect_data_files('customtkinter')
except:
    pass

# Ищем ffmpeg для включения в сборку
ffmpeg_binaries = []
ffmpeg_paths = [
    os.path.join('ffmpeg', 'bin', 'ffmpeg.exe'),
    os.path.join('ffmpeg', 'bin', 'ffprobe.exe'),
    os.path.join('ffmpeg', 'ffmpeg.exe'),
    'ffmpeg.exe',
]
for fp in ffmpeg_paths:
    if os.path.exists(fp):
        # Определяем целевую директорию в _MEIPASS
        if 'bin' in fp:
            target_dir = 'ffmpeg/bin'
        else:
            target_dir = 'ffmpeg'
        ffmpeg_binaries.append((fp, target_dir))
        print(f"[SPEC] Found ffmpeg: {fp} -> {target_dir}")

if not ffmpeg_binaries:
    print("[SPEC] WARNING: ffmpeg.exe not found! Video+Audio merging will not work.")
    print("[SPEC] Place ffmpeg.exe in: ffmpeg/bin/ffmpeg.exe")
else:
    print(f"[SPEC] Total ffmpeg binaries: {len(ffmpeg_binaries)}")

a = Analysis(
    ['downloader.py'],
    pathex=[],
    binaries=ffmpeg_binaries,
    datas=[
        ('config.json', '.'),
    ] + ctk_datas,
    hiddenimports=[
        'customtkinter',
        'yt_dlp',
        'yt_dlp.extractor',
        'yt_dlp.extractor.youtube',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'json',
        'threading',
        'url_utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'scipy',
        'pytest',
        'unittest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Без консоли (оконное приложение)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='icon.ico',  # Раскомментируйте если есть иконка
)
