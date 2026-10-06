import os
import shutil
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
dist_sn = base_dir / "dist" / "SN_TOOL"

dist_sn.mkdir(parents=True, exist_ok=True)

# 1. Copy icon, configs, and admin tools
admin_sync_files = [
    "icon.ico", "license_config.json", "custom_keys.json", "admin_key_history.json",
    "generated_keys_log.txt", "ADMIN_KEY_GENERATOR.py", "admin_dashboard.py",
    "license_engine.py", "START_ADMIN_KEY_GENERATOR.bat"
]
for fname in admin_sync_files:
    src = base_dir / fname
    if src.exists():
        shutil.copy2(src, dist_sn / fname)

# Also copy ADMIN_KEY_GENERATOR.exe if available in dist/ADMIN_KEY_GENERATOR
admin_exe_src = base_dir / "dist" / "ADMIN_KEY_GENERATOR" / "ADMIN_KEY_GENERATOR.exe"
if admin_exe_src.exists():
    shutil.copy2(admin_exe_src, dist_sn / "ADMIN_KEY_GENERATOR.exe")

# 2. Write START_SN_TOOL.bat
start_bat = """@echo off
chcp 65001 > nul
cd /d "%~dp0"
title 🎬 SN TOOL - STUDIO PRO
color 0b
cls

echo ========================================================================
echo  🎬 កំពុងដំណើរការ SN TOOL - STUDIO PRO (Khmer AI Drama Voice Studio)...
echo ========================================================================
echo.

start "" "%~dp0SN_TOOL.exe"
exit
"""
(dist_sn / "START_SN_TOOL.bat").write_text(start_bat, encoding="utf-8")

# 3. Write CREATE_DESKTOP_SHORTCUT.bat and copy create_shortcut.ps1
shortcut_bat = """@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0create_shortcut.ps1"
"""
(dist_sn / "CREATE_DESKTOP_SHORTCUT.bat").write_text(shortcut_bat, encoding="utf-8")

src_ps1 = base_dir / "scripts" / "create_shortcut.ps1"
if src_ps1.exists():
    shutil.copy2(src_ps1, dist_sn / "create_shortcut.ps1")

# 4. Copy data directory to both root and _internal
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

internal_data = dist_sn / "_internal" / "data"
if internal_data.exists():
    for fname in data_files:
        src = base_dir / "data" / fname
        if src.exists():
            shutil.copy2(src, internal_data / fname)

# 5. Copy static to both root and _internal
static_dst = dist_sn / "static"
if static_dst.exists():
    shutil.rmtree(static_dst)
shutil.copytree(base_dir / "static", static_dst)

internal_static = dist_sn / "_internal" / "static"
if internal_static.exists():
    shutil.rmtree(internal_static)
shutil.copytree(base_dir / "static", internal_static)

# 6. Ensure cache dir exists
(dist_sn / "cache").mkdir(parents=True, exist_ok=True)

# 7. Sync dist/ADMIN_KEY_GENERATOR static assets & configs
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

print("[OK] dist/SN_TOOL and dist/ADMIN_KEY_GENERATOR are completely synchronized and ready for production distribution!")
