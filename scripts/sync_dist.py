import os
import shutil
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
dist_sn = base_dir / "dist" / "SN_TOOL"

dist_sn.mkdir(parents=True, exist_ok=True)

# 1. Copy icon and configs for SN_TOOL (Do NOT copy license.key so clients are unactivated!)
sn_sync_files = [
    "icon.ico", "license_config.json", "custom_keys.json", "version.json", "server.py",
    "downloader.py", "vocal_remover.py", "hongguo_service.py", "shortmax_service.py", "reelshort_service.py",
    "hongguo_db.py", "license_engine.py", "video_processor.py", "pipeline.py", "batch_engine.py",
    "tts_engine.py", "audio_processor.py", "update.py", "translator.py", "stt_engine.py"
]
for fname in sn_sync_files:
    src = base_dir / fname
    if src.exists():
        shutil.copy2(src, dist_sn / fname)
        if (dist_sn / "_internal").exists():
            shutil.copy2(src, dist_sn / "_internal" / fname)

# Remove any accidental license.key from distribution folders
for lic in [dist_sn / "license.key", dist_sn / "_internal" / "license.key"]:
    if lic.exists():
        lic.unlink(missing_ok=True)

# 2. Write START_SN_TOOL.bat with auto-healing
start_bat = """@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
title 🎬 SN TOOL - STUDIO PRO
color 0e
cls

echo ========================================================================
echo  🎬 Launching SN TOOL - STUDIO PRO (AI Drama Dubbing Studio)...
echo ========================================================================
echo.

if not exist "%~dp0SN_TOOL.exe" (
    if exist "%~dp0SN_TOOL.exe.bak" (
        echo [INFO] Auto-restoring SN_TOOL.exe from backup...
        copy /y "%~dp0SN_TOOL.exe.bak" "%~dp0SN_TOOL.exe" >nul 2>&1
    )
)

if exist "%~dp0SN_TOOL.exe" (
    start "" "%~dp0SN_TOOL.exe"
    exit
)

if exist "%~dp0..\\..\\SN_TOOL.bat" (
    echo [INFO] Launching via SN_TOOL.bat...
    call "%~dp0..\\..\\SN_TOOL.bat"
    goto :END
)

if exist "%~dp0..\\..\\desktop_app.py" (
    where python >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        python "%~dp0..\\..\\desktop_app.py"
        goto :END
    )
    py -3.14 "%~dp0..\\..\\desktop_app.py"
    goto :END
)

echo.
echo ========================================================================
echo  ⚠️ SN_TOOL.exe not found!
echo  🛡️  Cause: Windows Defender / Antivirus may have quarantined the file.
echo  👉 Resolution:
echo     1. Open Windows Security -> Virus & threat protection -> Protection history
echo     2. Locate recent blocked item -> Actions -> Allow on device
echo     3. Or launch using "SN_TOOL.bat" in workspace root directly!
echo ========================================================================
pause

:END
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
