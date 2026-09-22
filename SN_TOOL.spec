# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path

ROOT_DIR = Path(SPECPATH).resolve()
import imageio_ffmpeg
ffmpeg_binaries_dir = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())

a = Analysis(
    [str(ROOT_DIR / 'desktop_app.py')],
    pathex=[str(ROOT_DIR)],
    binaries=[],
    datas=[
        (str(ROOT_DIR / 'static'), 'static'),
        (ffmpeg_binaries_dir, 'imageio_ffmpeg/binaries'),
    ],
    hiddenimports=[
        'edge_tts', 'pydub', 'flask', 'jinja2', 'soundfile', 'httpx',
        'webview', 'clr_loader', 'pythonnet', 'license_engine',
        'video_processor', 'downloader', 'tts_engine', 'translator',
        'pipeline', 'recap_engine', 'batch_engine', 'audio_processor',
        'vocal_remover', 'server'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

icon_path = str(ROOT_DIR / 'icon.ico') if (ROOT_DIR / 'icon.ico').exists() else None

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SN_TOOL',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[icon_path] if icon_path else None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SN_TOOL',
)

