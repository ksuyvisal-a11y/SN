import os
import shutil
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
dist_sn = base_dir / "dist" / "SN_TOOL"

dist_sn.mkdir(parents=True, exist_ok=True)

# 1. Copy icon and configs
for fname in ["icon.ico", "license.key", "license_config.json"]:
    src = base_dir / fname
    if src.exists():
        shutil.copy2(src, dist_sn / fname)

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

# 3. Write CREATE_DESKTOP_SHORTCUT.bat
shortcut_bat = """@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ========================================================================
echo  📌 កំពុងបង្កើតផ្លូវកាត់លើ Desktop សម្រាប់ SN TOOL (Desktop Shortcut)...
echo ========================================================================

powershell -Command ^
    "$ws = New-Object -ComObject WScript.Shell; " ^
    "$s = \\"$env:USERPROFILE\\Desktop\\SN TOOL - STUDIO PRO.lnk\\"; " ^
    "$sc = $ws.CreateShortcut($s); " ^
    "$sc.TargetPath = \\"%~dp0SN_TOOL.exe\\"; " ^
    "$sc.WorkingDirectory = \\"%~dp0\\"; " ^
    "$sc.IconLocation = \\"%~dp0icon.ico,0\\"; " ^
    "$sc.Description = \\"SN TOOL - STUDIO PRO (Khmer AI Drama Voice Studio)\\"; " ^
    "$sc.Save()"

echo.
echo [OK] បង្កើត Desktop Shortcut ជោគជ័យ!
timeout /t 3 > nul
"""
(dist_sn / "CREATE_DESKTOP_SHORTCUT.bat").write_text(shortcut_bat, encoding="utf-8")

# 4. Copy data directory to both root and _internal
data_dst = dist_sn / "data"
data_dst.mkdir(parents=True, exist_ok=True)
data_files = [
    "hongguo_catalog.db", "story_config.json", "drama_dictionary.json",
    "shortmax_all_dramas.json", "reelshort_all_dramas.json", "ai_dramas_streams.json",
    "ai_provider_config.json"
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

print("[OK] dist/SN_TOOL is completely synchronized and ready for production distribution!")
