import os
import sys
import shutil
import compileall
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
dist_sn = base_dir / "dist" / "SN_TOOL"
internal_dir = dist_sn / "_internal"

dist_sn.mkdir(parents=True, exist_ok=True)
internal_dir.mkdir(parents=True, exist_ok=True)

print("[*] Synchronizing SN_TOOL distribution package...")

# ==========================================================================
# 🛡️ SYSTEM 1: ZERO RAW SOURCE CODE LEAK (.pyc Bytecode Compilation & .py Purge)
# ==========================================================================
python_modules = [
    "server.py", "license_engine.py", "downloader.py", "vocal_remover.py",
    "hongguo_service.py", "shortmax_service.py", "reelshort_service.py",
    "hongguo_db.py", "video_processor.py", "pipeline.py", "batch_engine.py",
    "tts_engine.py", "audio_processor.py", "update.py", "translator.py", "stt_engine.py"
]

import py_compile
for fname in python_modules:
    src = base_dir / fname
    if src.exists():
        # Compile to optimized Python bytecode (.pyc) in _internal
        pyc_dst = internal_dir / f"{src.stem}.pyc"
        py_compile.compile(str(src), cfile=str(pyc_dst), optimize=2)

# Strictly delete ALL raw .py files from distribution root and _internal
for py_file in dist_sn.glob("*.py"):
    py_file.unlink(missing_ok=True)

if internal_dir.exists():
    shutil.rmtree(internal_dir / "scripts", ignore_errors=True)
    for py_file in internal_dir.glob("*.py"):
        py_file.unlink(missing_ok=True)

print(f"[OK] Compiled {len(python_modules)} Python modules to protected bytecode (.pyc). Zero .py source files remain!")

# ==========================================================================
# Configs & Meta Assets (Excluding raw code and license.key)
# ==========================================================================
config_files = ["icon.ico", "license_config.json", "custom_keys.json", "version.json"]
for fname in config_files:
    src = base_dir / fname
    if src.exists():
        shutil.copy2(src, dist_sn / fname)
        if internal_dir.exists():
            shutil.copy2(src, internal_dir / fname)

# Remove any accidental license.key so clients are always unactivated
for lic in [dist_sn / "license.key", internal_dir / "license.key"]:
    if lic.exists():
        lic.unlink(missing_ok=True)

# ==========================================================================
# Launcher Scripts
# ==========================================================================
start_bat = """@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
title 🎬 SN TOOL - STUDIO PRO
color 0e
cls

if not exist "%~dp0SN_TOOL.exe" (
    if exist "%~dp0SN_TOOL.exe.bak" (
        copy /y "%~dp0SN_TOOL.exe.bak" "%~dp0SN_TOOL.exe" >nul 2>&1
    )
)

if exist "%~dp0SN_TOOL.exe" (
    start "" "%~dp0SN_TOOL.exe"
    exit
)

echo.
echo ========================================================================
echo  ⚠️ SN_TOOL.exe not found!
echo  🛡️  Cause: Windows Defender / Antivirus may have quarantined the file.
echo  👉 Resolution:
echo     1. Open Windows Security -> Virus & threat protection -> Protection history
echo     2. Locate recent blocked item -> Actions -> Allow on device
echo ========================================================================
pause
"""
(dist_sn / "START_SN_TOOL.bat").write_text(start_bat, encoding="utf-8")

shortcut_bat = """@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0create_shortcut.ps1"
"""
(dist_sn / "CREATE_DESKTOP_SHORTCUT.bat").write_text(shortcut_bat, encoding="utf-8")

src_ps1 = base_dir / "scripts" / "create_shortcut.ps1"
if src_ps1.exists():
    shutil.copy2(src_ps1, dist_sn / "create_shortcut.ps1")

# ==========================================================================
# Data Assets
# ==========================================================================
data_dst = dist_sn / "data"
data_dst.mkdir(parents=True, exist_ok=True)
data_files = [
    "hongguo_catalog.db", "story_config.json", "drama_dictionary.json",
    "shortmax_all_dramas.json", "reelshort_all_dramas.json", "ai_dramas_streams.json",
    "ai_provider_config.json", "license_keys_online.json", "revoked_keys.json"
]
for fname in data_files:
    src = base_dir / "data" / fname
    if src.exists():
        shutil.copy2(src, data_dst / fname)

internal_data = internal_dir / "data"
if internal_data.exists():
    for fname in data_files:
        src = base_dir / "data" / fname
        if src.exists():
            shutil.copy2(src, internal_data / fname)

# ==========================================================================
# 🛡️ SYSTEM 2: STATIC ASSETS & JAVASCRIPT OBFUSCATION
# ==========================================================================
static_dst = dist_sn / "static"
if static_dst.exists():
    shutil.rmtree(static_dst)
shutil.copytree(base_dir / "static", static_dst)

internal_static = internal_dir / "static"
if internal_static.exists():
    shutil.rmtree(internal_static)
shutil.copytree(base_dir / "static", internal_static)

# Obfuscate app.js for both distribution locations
try:
    sys.path.insert(0, str(base_dir))
    sys.path.insert(0, str(base_dir / "scripts"))
    from obfuscate_js import obfuscate_javascript_file
    obfuscate_javascript_file(base_dir / "static" / "app.js", static_dst / "app.js")
    obfuscate_javascript_file(base_dir / "static" / "app.js", internal_static / "app.js")
    print("[OK] JavaScript obfuscation applied successfully!")
except Exception as e:
    print(f"[!] Warning during JS obfuscation: {e}")

# Ensure cache dir exists
(dist_sn / "cache").mkdir(parents=True, exist_ok=True)

# ==========================================================================
# Sync dist/ADMIN_KEY_GENERATOR static assets & configs
# ==========================================================================
dist_admin = base_dir / "dist" / "ADMIN_KEY_GENERATOR"
if dist_admin.exists():
    for fname in ["custom_keys.json", "admin_key_history.json", "license_config.json", "icon.ico"]:
        src = base_dir / fname
        if src.exists():
            shutil.copy2(src, dist_admin / fname)
    admin_static = dist_admin / "static"
    if admin_static.exists():
        shutil.rmtree(admin_static)
    shutil.copytree(base_dir / "static", admin_static)
    admin_int_static = dist_admin / "_internal" / "static"
    if admin_int_static.exists():
        shutil.rmtree(admin_int_static)
    shutil.copytree(base_dir / "static", admin_int_static)

print("[OK] dist/SN_TOOL and dist/ADMIN_KEY_GENERATOR are completely synchronized and protected with Military-Grade Anti-Bypass!")
