import os
import sys
import zipfile
import shutil
from pathlib import Path

def package_update_zip():
    base_dir = Path(__file__).resolve().parent.parent
    zip_path = base_dir / "SN_TOOL_UPDATE.zip"
    temp_zip = base_dir / "SN_TOOL_UPDATE.tmp.zip"
    
    print(f"[*] Packaging {zip_path.name}...")
    
    include_root_files = [
        "version.json", "icon.ico", "license_config.json", "custom_keys.json",
        "admin_key_history.json", "revoked_keys.json",
        "SN_TOOL.bat", "START_ADMIN_KEY_GENERATOR.bat", "START_ADMIN_DASHBOARD.bat",
        "CREATE_DESKTOP_SHORTCUT.bat", "Khmer_Drama_Studio_Launcher.bat", "LAUNCH_STUDIO_SILENT.vbs"
    ]
    
    if temp_zip.exists():
        temp_zip.unlink(missing_ok=True)
        
    with zipfile.ZipFile(temp_zip, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        # 1. Add all .py files in root
        for py_file in base_dir.glob("*.py"):
            arcname = py_file.name
            zf.write(py_file, arcname)
            
        # 2. Add specific root files
        for fname in include_root_files:
            fpath = base_dir / fname
            if fpath.exists():
                zf.write(fpath, fname)
                
        # 3. Add static folder
        static_dir = base_dir / "static"
        if static_dir.exists():
            for root, dirs, files in os.walk(static_dir):
                for f in files:
                    full_p = Path(root) / f
                    rel_p = full_p.relative_to(base_dir)
                    zf.write(full_p, str(rel_p).replace('\\', '/'))
                    
        # 4. Add data folder (exclude heavy databases and temporary caches)
        data_dir = base_dir / "data"
        if data_dir.exists():
            for root, dirs, files in os.walk(data_dir):
                if any(ex in Path(root).parts for ex in ["uploads", "exports", "cache", "projects"]):
                    continue
                for f in files:
                    if f.endswith(('.tmp', '.log', '.db', '.sqlite')):
                        continue
                    full_p = Path(root) / f
                    rel_p = full_p.relative_to(base_dir)
                    zf.write(full_p, str(rel_p).replace('\\', '/'))
                    
        # 5. Add scripts folder
        scripts_dir = base_dir / "scripts"
        if scripts_dir.exists():
            for root, dirs, files in os.walk(scripts_dir):
                if "__pycache__" in root:
                    continue
                for f in files:
                    full_p = Path(root) / f
                    rel_p = full_p.relative_to(base_dir)
                    zf.write(full_p, str(rel_p).replace('\\', '/'))

    # Replace target zip
    try:
        if zip_path.exists():
            zip_path.unlink()
        temp_zip.rename(zip_path)
    except Exception:
        shutil.move(str(temp_zip), str(zip_path))
        
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"[OK] Successfully created {zip_path.name} ({size_mb:.2f} MB)")

if __name__ == "__main__":
    package_update_zip()
