# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['D:/folder My Project/SN/desktop_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('D:/folder My Project/SN/static', 'static'),
        ('C:/Users/TUF/AppData/Local/Programs/Python/Python312/Lib/site-packages/imageio_ffmpeg/binaries', 'imageio_ffmpeg/binaries')
    ],
    hiddenimports=['edge_tts', 'pydub', 'flask', 'jinja2', 'soundfile', 'httpx', 'webview', 'clr_loader', 'pythonnet', 'license_engine', 'video_processor', 'downloader', 'tts_engine', 'translator', 'pipeline', 'recap_engine', 'batch_engine'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

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
    icon=['D:/folder My Project/SN/icon.ico'],
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
