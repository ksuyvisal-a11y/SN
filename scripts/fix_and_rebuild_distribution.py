"""
Fix and rebuild full distribution for SN TOOL (v1.0.6)
Ensures dist/SN_TOOL has the full PyInstaller runtime, SN_TOOL.exe, and packages
a truly standalone, working SN_TOOL_Portable.zip.
"""

import os
import sys
import shutil
import zipfile
from pathlib import Path

def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    base_dir = Path(__file__).resolve().parent.parent
    local_app_data = os.environ.get("LOCALAPPDATA", r"C:\Users\M\AppData\Local")
    installed_dir = Path(local_app_data) / "Programs" / "SN_TOOL"
    dist_dir = base_dir / "dist" / "SN_TOOL"
    dist_internal = dist_dir / "_internal"

    print("=" * 65)
    print("  🚀 SN TOOL - REBUILDING 100% COMPLETE PORTABLE DISTRIBUTION")
    print("=" * 65)

    dist_dir.mkdir(parents=True, exist_ok=True)
    dist_internal.mkdir(parents=True, exist_ok=True)

    # 1. Copy SN_TOOL.exe and SN_TOOL.exe.bak
    for exe_name in ["SN_TOOL.exe", "SN_TOOL.exe.bak"]:
        src_exe = installed_dir / exe_name
        if not src_exe.exists():
            src_exe = base_dir / exe_name
        if src_exe.exists():
            dst_exe = dist_dir / exe_name
            shutil.copy2(src_exe, dst_exe)
            print(f"[OK] Copied executable: {exe_name} ({dst_exe.stat().st_size / (1024*1024):.2f} MB)")
        else:
            print(f"[!] Warning: Could not find {exe_name}")

    # 2. Sync full runtime from installed _internal (DLLs, pyds, libraries)
    installed_internal = installed_dir / "_internal"
    if installed_internal.exists():
        print("[*] Synchronizing complete runtime libraries & DLLs...")
        copied_count = 0
        for root, dirs, files in os.walk(installed_internal):
            rel_path = Path(root).relative_to(installed_internal)
            target_dir = dist_internal / rel_path
            target_dir.mkdir(parents=True, exist_ok=True)
            for f in files:
                if f.lower() == "license.key":
                    continue
                src_file = Path(root) / f
                dst_file = target_dir / f
                if not dst_file.exists() or src_file.stat().st_mtime > dst_file.stat().st_mtime:
                    shutil.copy2(src_file, dst_file)
                    copied_count += 1
        print(f"[OK] Synced {copied_count} runtime files to dist/SN_TOOL/_internal")

    # 3. Ensure launcher scripts exist in dist
    start_bat_path = dist_dir / "START_SN_TOOL.bat"
    if not start_bat_path.exists():
        src_bat = base_dir / "START_SN_TOOL.bat"
        if src_bat.exists():
            shutil.copy2(src_bat, start_bat_path)

    # 4. Strictly remove license.key from dist so clients start unactivated
    for lic in [dist_dir / "license.key", dist_internal / "license.key"]:
        if lic.exists():
            lic.unlink(missing_ok=True)

    # 5. Build True Standalone SN_TOOL_Portable.zip
    portable_zip = base_dir / "dist" / "SN_TOOL_Portable.zip"
    temp_zip = base_dir / "dist" / "SN_TOOL_Portable.tmp.zip"
    print(f"\n[*] Packaging 100% COMPLETE Portable Zip: {portable_zip.name}...")
    
    if temp_zip.exists():
        temp_zip.unlink(missing_ok=True)

    file_count = 0
    with zipfile.ZipFile(temp_zip, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=4) as zf:
        for root, dirs, files in os.walk(dist_dir):
            for f in files:
                if f.lower() == "license.key":
                    continue
                full_p = Path(root) / f
                rel_p = full_p.relative_to(dist_dir)
                archive_name = f"SN_TOOL/{str(rel_p).replace(chr(92), '/')}"
                zf.write(full_p, archive_name)
                file_count += 1

    if portable_zip.exists():
        portable_zip.unlink(missing_ok=True)
    temp_zip.rename(portable_zip)

    size_mb = portable_zip.stat().st_size / (1024 * 1024)
    print("=" * 65)
    print(f"  🎉 SUCCESS: {portable_zip.name} READY!")
    print(f"  📦 Total Files inside Zip: {file_count}")
    print(f"  💿 Zip File Size: {size_mb:.2f} MB")
    print("=" * 65)

if __name__ == "__main__":
    main()
