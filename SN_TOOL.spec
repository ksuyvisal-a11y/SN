# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path

ROOT_DIR = Path(SPECPATH).resolve()
import imageio_ffmpeg
ffmpeg_binaries_dir = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())

import faster_whisper
import huggingface_hub
faster_whisper_dir = os.path.dirname(faster_whisper.__file__)
faster_whisper_assets = os.path.join(faster_whisper_dir, 'assets')
huggingface_hub_dir = os.path.dirname(huggingface_hub.__file__)

a = Analysis(
    [str(ROOT_DIR / 'desktop_app.py')],
    pathex=[str(ROOT_DIR)],
    binaries=[],
    datas=[
        (str(ROOT_DIR / 'icon.ico'), '.'),
        (str(ROOT_DIR / 'static'), 'static'),
        (str(ROOT_DIR / 'scripts'), 'scripts'),
        (str(ROOT_DIR / 'data' / 'hongguo_catalog.db'), 'data'),
        (str(ROOT_DIR / 'data' / 'shortmax_all_dramas.json'), 'data'),
        (str(ROOT_DIR / 'data' / 'reelshort_all_dramas.json'), 'data'),
        (str(ROOT_DIR / 'data' / 'ai_dramas_streams.json'), 'data'),
        (str(ROOT_DIR / 'data' / 'story_config.json'), 'data'),
        (str(ROOT_DIR / 'data' / 'drama_dictionary.json'), 'data'),
        (str(ROOT_DIR / 'data' / 'ai_provider_config.json'), 'data'),
        (ffmpeg_binaries_dir, 'imageio_ffmpeg/binaries'),
        (faster_whisper_assets, 'faster_whisper/assets'),
        (faster_whisper_dir, 'faster_whisper'),
        (huggingface_hub_dir, 'huggingface_hub'),
    ],
    hiddenimports=[
        'edge_tts', 'pydub', 'flask', 'jinja2', 'soundfile', 'httpx',
        'webview', 'clr_loader', 'pythonnet', 'license_engine',
        'video_processor', 'downloader', 'tts_engine', 'translator',
        'pipeline', 'recap_engine', 'batch_engine', 'audio_processor',
        'vocal_remover', 'server', 'stt_engine', 'faster_whisper',
        'huggingface_hub', 'tokenizers', 'onnxruntime', 'ctranslate2',
        'hongguo_service', 'hongguo_db', 'shortmax_service', 'reelshort_service',
        'cryptography'
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

