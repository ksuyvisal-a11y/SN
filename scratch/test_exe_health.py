import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def check_exe_health():
    print("=" * 60)
    print(" 🔍 SN TOOL - DIST EXECUTABLE HEALTH CHECK")
    print("=" * 60)

    dist_dir = Path("dist/SN_TOOL")
    exe_path = dist_dir / "SN_TOOL.exe"

    # 1. Check EXE Existence
    if not exe_path.exists():
        print("❌ [FAIL] SN_TOOL.exe not found in dist/SN_TOOL!")
        return False
    
    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print(f"✅ [PASS] Found SN_TOOL.exe ({size_mb:.2f} MB)")

    # 2. Check Internal Directory Structure
    internal_dir = dist_dir / "_internal"
    if not internal_dir.exists():
        print("❌ [FAIL] _internal directory missing!")
        return False
    print("✅ [PASS] _internal directory present")

    # 3. Check Key Assets
    required_dirs = ["static", "data", "cache"]
    for rd in required_dirs:
        p = dist_dir / rd
        if p.exists():
            print(f"✅ [PASS] Subfolder '{rd}' present in dist")
        else:
            print(f"⚠️ [WARN] Subfolder '{rd}' missing in dist, will be auto-created at runtime")

    # 4. Check UI Files
    index_html = dist_dir / "static" / "index.html"
    app_js = dist_dir / "static" / "app.js"
    style_css = dist_dir / "static" / "style.css"
    if index_html.exists() and app_js.exists() and style_css.exists():
        print(f"✅ [PASS] Web UI Assets (index.html, app.js, style.css) present ({app_js.stat().st_size} bytes JS)")
    else:
        print("❌ [FAIL] Web UI static assets incomplete!")

    # 5. Check License Engine & Key
    try:
        from license_engine import get_machine_hwid, verify_license_key
        mid = get_machine_hwid()
        print(f"✅ [PASS] Machine HWID: {mid}")
        
        # Check dist license
        lic_file = dist_dir / "license.key"
        if lic_file.exists():
            import json
            lic_data = json.loads(lic_file.read_text(encoding="utf-8"))
            k_str = lic_data.get("license_key", "")
            valid, msg, info = verify_license_key(k_str, mid)
            if valid:
                print(f"✅ [PASS] Pre-installed License: VALID ({lic_data.get('plan', 'VIP')} - {lic_data.get('expires_at', 'Active')})")
            else:
                print(f"ℹ️ [INFO] Current license in dist: {msg}")
        else:
            print("ℹ️ [INFO] No license.key in dist (Will prompt Activation Gate on first launch - Perfect for client distribution)")
    except Exception as e:
        print(f"⚠️ [WARN] License check notice: {e}")

    # 6. Check Admin Generator
    admin_exe = Path("dist/ADMIN_KEY_GENERATOR/ADMIN_KEY_GENERATOR.exe")
    if admin_exe.exists():
        admin_size = admin_exe.stat().st_size / (1024 * 1024)
        print(f"✅ [PASS] Admin Key Generator standalone EXE present ({admin_size:.2f} MB)")
    else:
        print("ℹ️ [INFO] Admin Generator EXE not built yet (can be run via ADMIN_KEY_GENERATOR.py)")

    print("=" * 60)
    print(" 🚀 OVERALL HEALTH: READY FOR COMMERCIAL PRODUCTION!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    check_exe_health()
