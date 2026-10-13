import os
import sys
import json
import shutil
import datetime
import subprocess
from pathlib import Path

def run_step(cmd_list, desc):
    print(f"\n[*] {desc}...")
    res = subprocess.run(cmd_list, cwd=str(Path(__file__).resolve().parent.parent))
    if res.returncode != 0:
        print(f"[!] Warning: Step failed with return code {res.returncode}")
    else:
        print(f"[OK] {desc} completed successfully.")

def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stdin.reconfigure(encoding="utf-8")
        except Exception:
            pass

    base_dir = Path(__file__).resolve().parent.parent
    vjson_path = base_dir / "version.json"
    update_py_path = base_dir / "update.py"

    print("=" * 65)
    print("  🚀 SN TOOL - 1-CLICK UPDATE & RELEASE CREATOR (Khmer Edition)")
    print("=" * 65)

    current_ver = "1.0.2"
    vdata = {}
    if vjson_path.exists():
        try:
            with open(vjson_path, "r", encoding="utf-8") as f:
                vdata = json.load(f)
                current_ver = vdata.get("version", current_ver)
        except Exception:
            pass

    print(f"\n📌 Version បច្ចុប្បន្ន: v{current_ver}")
    print("-----------------------------------------------------------------")
    print(f"👉 វាយលេខ Version ថ្មី (ចុច Enter ភ្លាម ប្រសិនបើចង់រក្សាទុក v{current_ver}):")
    new_ver_input = input(f"New Version [Enter for v{current_ver}]: ").strip()
    new_ver = new_ver_input.lstrip("vV") if new_ver_input else current_ver

    # Update version.json
    today_str = datetime.date.today().isoformat()
    vdata["version"] = new_ver
    vdata["release_date"] = today_str
    vdata["title"] = f"SN TOOL STUDIO PRO - Official Update v{new_ver}"
    vdata["download_url"] = "https://github.com/ksuyvisal-a11y/SN/releases/latest/download/SN_TOOL_Setup.exe"
    
    with open(vjson_path, "w", encoding="utf-8") as f:
        json.dump(vdata, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] បានកែសម្រួល version.json ទៅជា v{new_ver} ({today_str})")

    # Update CURRENT_VERSION in update.py
    if update_py_path.exists():
        try:
            content = update_py_path.read_text(encoding="utf-8")
            import re
            new_content = re.sub(r'CURRENT_VERSION\s*=\s*"[^"]+"', f'CURRENT_VERSION = "{new_ver}"', content, count=1)
            update_py_path.write_text(new_content, encoding="utf-8")
            print(f"[OK] បានកែសម្រួល update.py CURRENT_VERSION ទៅជា v{new_ver}")
        except Exception as e:
            print(f"[!] Warning updating update.py: {e}")

    # 1. Sync dist folders
    run_step([sys.executable, str(base_dir / "scripts" / "sync_dist.py")], "Synchronizing static and configs to dist/")

    # 2. Package update zip (as backup patch)
    run_step([sys.executable, str(base_dir / "scripts" / "package_update_zip.py")], "Packaging backup patch SN_TOOL_UPDATE.zip")

    # 3. Build single-file installer SN_TOOL_Setup.exe
    run_step([sys.executable, str(base_dir / "scripts" / "build_installer.py")], "Compiling 1-File Standalone Setup (SN_TOOL_Setup.exe)")

    target_installer = base_dir / "dist" / "SN_TOOL_Setup.exe"

    print("\n" + "=" * 65)
    print("  🎉 រួចរាល់ ១០០%! ឯកសារ 1-FILE RELEASE ត្រូវបានបង្កើតរួចរាល់")
    print("=" * 65)
    if target_installer.exists():
        print(f"  💿 File តែមួយគត់សម្រាប់ Release: dist/{target_installer.name} ({target_installer.stat().st_size / (1024*1024):.2f} MB)")

    print("\n-----------------------------------------------------------------")
    print("  👉 របៀបបញ្ជូនទៅកាន់ GitHub Release (1 File ងាយស្រួលបំផុត):")
    print("     1. បើក GitHub Release: https://github.com/ksuyvisal-a11y/SN/releases/new")
    print(f"     2. ដាក់ Tag: v{new_ver}")
    print(f"     3. ទម្លាក់តែ ១ File គត់គឺ '{target_installer.name}' ចូលជាការស្រេច!")
    print("     👉 ទាំង Client ថ្មី (ដំឡើងដំបូង) និង Client ចាស់ (ចុច Check Updates) គឺដំណើរការតាម File មួយនេះទាំងអស់!")
    print("-----------------------------------------------------------------\n")

    # Automatically highlight SN_TOOL_Setup.exe in Explorer
    try:
        subprocess.run(f'explorer /select,"{target_installer}"', shell=True)
    except Exception:
        pass

if __name__ == "__main__":
    main()
