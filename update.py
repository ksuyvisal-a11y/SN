"""
SN_TOOL - GitHub Auto Update Engine & Version Manager
Supports 1-Click Version Updates via GitHub Releases & Repository
"""

import os
import sys
import json
import time
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, Tuple

CURRENT_VERSION = "1.0.5"
GITHUB_OWNER = "ksuyvisal-a11y"
GITHUB_REPO = "SN"
UPDATE_CHECK_RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/main/version.json"
GITHUB_API_RELEASE_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"

def parse_version_tuple(ver_str: str) -> Tuple[int, ...]:
    """Parse '5.1.0' into (5, 1, 0) tuple for accurate comparison."""
    try:
        clean = str(ver_str).strip().lstrip("vV")
        parts = [int(p) for p in clean.split(".") if p.isdigit()]
        return tuple(parts) if parts else (0, 0, 0)
    except Exception:
        return (0, 0, 0)

def is_newer_version(remote_ver: str, local_ver: str = CURRENT_VERSION) -> bool:
    """Return True if remote_ver is strictly newer than local_ver."""
    return parse_version_tuple(remote_ver) > parse_version_tuple(local_ver)

def get_local_version() -> str:
    """Read local version from version.json if present, else fallback to CURRENT_VERSION."""
    candidates = [
        Path(__file__).resolve().parent / "version.json",
        Path.cwd() / "version.json",
    ]
    if getattr(sys, "frozen", False):
        candidates.insert(0, Path(sys.executable).parent / "version.json")
    for local_vjson in candidates:
        try:
            if local_vjson.exists():
                with open(local_vjson, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    ver = data.get("version")
                    if ver:
                        return str(ver)
        except Exception:
            pass
    return CURRENT_VERSION

def check_for_updates(github_token: str = None) -> Dict[str, Any]:
    """
    Check GitHub for newer versions of SN_TOOL.
    Checks raw version.json first, falls back to GitHub releases API.
    """
    local_ver = get_local_version()
    headers = {
        "User-Agent": "SN_TOOL-Updater/5.0",
        "Accept": "application/json"
    }
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    # 1. Try raw version.json on main branch
    try:
        req = urllib.request.Request(UPDATE_CHECK_RAW_URL, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                remote_ver = data.get("version", local_ver)
                has_update = is_newer_version(remote_ver, local_ver)
                return {
                    "success": True,
                    "has_update": has_update,
                    "current_version": local_ver,
                    "latest_version": remote_ver,
                    "title": data.get("title", f"SN TOOL v{remote_ver}"),
                    "release_notes": data.get("release_notes", "General system improvements and performance optimizations"),
                    "download_url": data.get("download_url", ""),
                    "release_date": data.get("release_date", ""),
                    "channel": data.get("channel", "stable")
                }
    except urllib.error.HTTPError as he:
        # If 404, repo might be private without token or file not pushed yet
        if he.code == 404:
            pass
    except Exception:
        pass

    # 2. Fallback to GitHub Releases API
    try:
        req = urllib.request.Request(GITHUB_API_RELEASE_URL, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as response:
            if response.status == 200:
                rel = json.loads(response.read().decode("utf-8"))
                tag_name = rel.get("tag_name", "").lstrip("vV")
                remote_ver = tag_name or local_ver
                has_update = is_newer_version(remote_ver, local_ver)
                download_url = ""
                # Prioritize single-file installer SN_TOOL_Setup.exe, then any .exe, then .zip
                for asset in rel.get("assets", []):
                    aname = asset.get("name", "").lower()
                    if aname == "sn_tool_setup.exe":
                        download_url = asset.get("browser_download_url", "")
                        break
                    elif aname.endswith(".exe"):
                        download_url = asset.get("browser_download_url", "")
                        break
                if not download_url:
                    for asset in rel.get("assets", []):
                        if asset.get("name", "").endswith(".zip"):
                            download_url = asset.get("browser_download_url", "")
                            break
                if not download_url:
                    download_url = rel.get("zipball_url", "")

                return {
                    "success": True,
                    "has_update": has_update,
                    "current_version": local_ver,
                    "latest_version": remote_ver,
                    "title": rel.get("name", f"SN TOOL v{remote_ver}"),
                    "release_notes": rel.get("body", "General system improvements and performance optimizations"),
                    "download_url": download_url,
                    "release_date": rel.get("published_at", "")[:10] if rel.get("published_at") else "",
                    "channel": "stable"
                }
    except Exception as e:
        pass

    # Default / Offline / Up-to-date response
    return {
        "success": True,
        "has_update": False,
        "current_version": local_ver,
        "latest_version": local_ver,
        "title": "SN TOOL STUDIO PRO",
        "release_notes": "You are running the latest version of SN TOOL STUDIO PRO.",
        "download_url": "",
        "channel": "stable"
    }

def apply_git_pull_update(app_dir: Path) -> Dict[str, Any]:
    """Execute git pull for source installations."""
    try:
        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            cwd=str(app_dir),
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=0x08000000 if sys.platform == "win32" else 0
        )
        if result.returncode == 0:
            return {
                "success": True,
                "message": "Git pull ជោគជ័យ! កម្មវិធីត្រូវបាន update ឡើងទៅ Version ថ្មីបំផុត។",
                "output": result.stdout
            }
        else:
            return {
                "success": False,
                "error": f"Git pull error: {result.stderr or result.stdout}"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

def apply_zip_download_update(download_url: str, app_dir: Path) -> Dict[str, Any]:
    """
    Download update (supports 1-File SN_TOOL_Setup.exe or update_package.zip) and launch detached updater script on Windows.
    """
    if not download_url:
        return {"success": False, "error": "No download URL provided for update."}

    cache_dir = app_dir / "data" / "cache" / "update"
    cache_dir.mkdir(parents=True, exist_ok=True)
    is_exe = download_url.lower().split("?")[0].endswith(".exe")
    dest_file = cache_dir / ("SN_TOOL_Setup.exe" if is_exe else "update_package.zip")

    try:
        # Download file
        req = urllib.request.Request(download_url, headers={"User-Agent": "SN_TOOL-Updater/5.0"})
        with urllib.request.urlopen(req, timeout=300) as resp, open(dest_file, "wb") as out_f:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                out_f.write(chunk)

        # Create detached batch script to launch installer or extract zip and restart
        bat_file = app_dir / "apply_update.bat"
        exe_file = app_dir / "SN_TOOL.exe"
        run_bat = app_dir / "START_SN_TOOL.bat"
        restart_cmd = f'start "" "{exe_file}"' if exe_file.exists() else f'start "" "{run_bat}"'

        if is_exe:
            bat_content = f"""@echo off
chcp 65001 >nul
echo [SN TOOL UPDATER] Launching Setup Update...
timeout /t 2 /nobreak >nul
start "" "{dest_file}"
del "%~f0" & exit
"""
        else:
            bat_content = f"""@echo off
chcp 65001 >nul
echo [SN TOOL UPDATER] Applying updates...
timeout /t 2 /nobreak >nul
tar -xf "{dest_file}" -C "{app_dir}" 2>nul || powershell -command "Expand-Archive -Path '{dest_file}' -DestinationPath '{app_dir}' -Force"
del /f /q "{dest_file}" 2>nul
echo [SN TOOL UPDATER] Update finished! Relaunching SN TOOL...
{restart_cmd}
del "%~f0" & exit
"""
        with open(bat_file, "w", encoding="utf-8") as f:
            f.write(bat_content)

        # Launch detached batch script
        if sys.platform == "win32":
            subprocess.Popen(
                ["cmd.exe", "/c", str(bat_file)],
                cwd=str(app_dir),
                creationflags=0x00000008 | 0x08000000
            )

        return {
            "success": True,
            "message": "ការទាញយកជោគជ័យ! កម្មវិធីនឹង Update ឡើង Version ថ្មីក្នុងរយៈពេល 2 វិនាទី..."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_version_info() -> Dict[str, Any]:
    return {
        "version": get_local_version(),
        "app_name": "SN TOOL - STUDIO PRO",
        "author": "SN Team Cambodia",
        "github_repo": f"{GITHUB_OWNER}/{GITHUB_REPO}"
    }

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    info = get_version_info()
    print("=" * 60)
    print(f" [*] {info['app_name']} - Version {info['version']}")
    print(f" GitHub Repo: https://github.com/{info['github_repo']}")
    print("=" * 60)
    res = check_for_updates()
    print(f" Update Available: {res.get('has_update')}")
    print(f" Latest Version: {res.get('latest_version')}")
    print("=" * 60)
