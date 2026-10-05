"""
===========================================================================
  🔐 SN STUDIO - ADMIN KEY GENERATOR & VIP LICENSE MANAGER
===========================================================================
This tool allows the Administrator to generate, list, and manage user License Keys.
"""

import sys
import os
import json
from pathlib import Path

# Enable UTF-8 encoding in Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from license_engine import (
    generate_license_key,
    verify_license_key,
    register_custom_key,
    revoke_license_key,
    unrevoke_license_key,
    get_revoked_keys,
    is_license_required,
    set_license_required,
    get_machine_hwid,
    sync_online_keys,
    ADMIN_HISTORY_FILE,
    GENERATED_KEYS_LOG,
    CUSTOM_KEYS_FILE,
    DEFAULT_MASTER_KEYS
)

import threading
import time
import urllib.request
ADMIN_PORT = 8888
ADMIN_URL = f"http://127.0.0.1:{ADMIN_PORT}/admin"

def is_server_running() -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{ADMIN_PORT}/api/license/status", timeout=1) as r:
            return r.status == 200
    except Exception:
        return False

def ensure_server_running(timeout: float = 6.0) -> bool:
    """Ensure dedicated Admin server is active on port 8888."""
    if is_server_running():
        return True
    def run_app():
        import logging
        from admin_dashboard import admin_app
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        admin_app.run(host="127.0.0.1", port=ADMIN_PORT, debug=False, use_reloader=False)
    t = threading.Thread(target=run_app, daemon=True)
    t.start()
    t_end = time.time() + timeout
    while time.time() < t_end:
        if is_server_running():
            return True
        time.sleep(0.2)
    return is_server_running()

def copy_to_clipboard(text: str):
    """Copy text to Windows clipboard."""
    try:
        if sys.platform == "win32":
            import subprocess
            subprocess.run("clip", input=text.encode("utf-8"), check=True)
    except Exception:
        pass

def print_header():
    lic_mode = "🟢 ON (ត្រូវវាយ Key ទើបប្រើបាន)" if is_license_required() else "🟡 OFF (Free Mode - ប្រើបានភ្លាមៗមិនបាច់ Key)"
    server_status = f"🟢 ដំណើរការស្រេច ({ADMIN_URL})" if is_server_running() else "🟡 កំពុងបើក..."
    print("\n" + "=" * 65)
    print(" 👑 SN STUDIO - ADMIN KEY GENERATOR (ប្រព័ន្ធគ្រប់គ្រង KEY ជូន USER)")
    print("=" * 65)
    print(f" 💻 Admin Machine HWID: {get_machine_hwid()}")
    print(f" 🛡️  License Gate Mode:  {lic_mode}")
    print(f" 🌐 Admin Dashboard:    {server_status}")
    print("=" * 65)

def print_key_card(record):
    msg = (
        f"\n=======================================================\n"
        f" 🎬 SN STUDIO - VIP LICENSE KEY\n"
        f"=======================================================\n"
        f" 👤 Client:  {record.get('client_name')}\n"
        f" 🔑 Key:     {record.get('license_key')}\n"
        f" 📦 Plan:    {record.get('plan')}\n"
        f" ⏳ Expiry:  {record.get('expires_at')}\n"
        f" 🔒 HWID:    {record.get('bound_hwid')}\n"
        f"=======================================================\n"
        f"👉 របៀបប្រើ៖ បើក SN STUDIO -> យក Key នេះ Paste ចូលរួចចុច Activate\n"
        f"======================================================="
    )
    print(msg)
    copy_to_clipboard(record.get('license_key', ''))
    print(" (✨ បាន Copy Key ចូល Clipboard ស្វ័យប្រវត្ត រួចជាស្រេច!)")

def interactive_menu():
    ensure_server_running()
    while True:
        print_header()
        print(" 🌐 ផ្នែកទី ១: WEB ADMIN DASHBOARD (ផ្ទាំងគ្រប់គ្រងលើ BROWSER)")
        print(" [1] បើកផ្ទាំង Admin Dashboard (http://127.0.0.1:8000/admin)")
        print("-" * 65)
        print(" 🔑 ផ្នែកទី ២: បង្កើត KEY ជូនអតិថិជន (KEY GENERATION)")
        print(" [2] បង្កើត License Key ថ្មី (កំណត់ចំនួនថ្ងៃ 30d, 90d, 1y, មួយជីវិត)")
        print(" [3] បង្កើត Custom Key ផ្ទាល់ខ្លួន (វាយអក្សរតាមចិត្ត ឧ. SAL-2026)")
        print(" [9] បង្កើត Lifetime Key មួយជីវិតភ្លាមៗ (Quick Lifetime VIP)")
        print("-" * 65)
        print(" 👥 ផ្នែកទី ៣: គ្រប់គ្រងអតិថិជន & BLOCK USER (MANAGEMENT)")
        print(" [4] បញ្ឈប់ / Block Key របស់ User (Revoke / Ban Key មិនឱ្យប្រើ)")
        print(" [5] ដោះសោ / Unban Key (Restore Key ឱ្យដំណើរការឡើងវិញ)")
        print(" [7] មើលប្រវត្តិ Key និងអតិថិជនទាំងអស់ (View All Keys History)")
        print(" [8] ត្រួតពិនិត្យ និង Verify License Key")
        print("-" * 65)
        print(" ⚙️ ផ្នែកទី ៤: ការកំណត់ GATE & SYSTEM (GATE SETTINGS)")
        print(" [6] បិទ / បើក ការទាមទារ Key (Toggle Free Mode vs Require Key)")
        print(" [S] 🔄 ធ្វើបច្ចុប្បន្នភាព Key Online ទាំងអស់ (Sync & Export Online Keys)")
        print(" [0] ចាកចេញពីកម្មវិធី (Exit)")
        print("=" * 65)
        
        choice = input("👉 សូមជ្រើសរើសជម្រើស (0-9 ឬ S): ").strip()

        if choice == "1":
            import webbrowser
            print("\n⏳ កំពុងត្រួតពិនិត្យ និងបើកដំណើរការ Admin Server (Port 8888)...")
            ready = ensure_server_running(timeout=6.0)
            url = ADMIN_URL
            if ready:
                print(f"🌐 Admin Server ដំណើរការរួចរាល់! កំពុងបើកផ្ទាំង Dashboard ក្នុង Browser ({url})...")
            else:
                print(f"⚠️ Admin Server កំពុងបើកយឺតបន្តិច ប៉ុន្តែកំពុងព្យាយាមបើក Browser ទៅកាន់៖ {url}")
            try:
                webbrowser.open(url)
            except Exception:
                pass
            print(f"✅ ប្រសិនបើ Browser មិនបើកដោយស្វ័យប្រវត្ត សូមចុចបើកតំណភ្ជាប់នេះ៖ {url}")
            input("\nចុច Enter ដើម្បីបន្ត...")

        elif choice == "2":
            client_name = input("\n👤 បញ្ចូលឈ្មោះ Client/User (ឧ. Sokha_FB): ").strip() or "VIP_Client"
            print("\nជ្រើសរើសកាលកំណត់ (Duration):")
            print(" [1] 30 ថ្ងៃ (1 Month)")
            print(" [2] 90 ថ្ងៃ (3 Months)")
            print(" [3] 365 ថ្ងៃ (1 Year)")
            print(" [4] ពេញមួយជីវិត (Lifetime VIP)")
            print(" [5] Trial 3 ថ្ងៃ (3-Day Trial)")
            print(" [6] វាយចំនួនថ្ងៃផ្ទាល់ខ្លួន (Custom Days ឧ. 5, 14, 60, 180...)")
            
            dur_choice = input("👉 ជ្រើសរើស (1-6): ").strip()
            if dur_choice == "6":
                try:
                    custom_d = int(input("👉 បញ្ចូលចំនួនថ្ងៃ (វាយ 0 សម្រាប់មួយជីវិត): ").strip() or "30")
                    days = custom_d
                    plan = f"VIP_{days}D" if days > 0 else "VIP_LIFETIME"
                except Exception:
                    days = 30
                    plan = "VIP_30D"
            else:
                days_map = {"1": 30, "2": 90, "3": 365, "4": 0, "5": 3}
                plan_map = {"1": "VIP_1M", "2": "VIP_3M", "3": "VIP_1Y", "4": "VIP_LIFETIME", "5": "TRIAL_3D"}
                days = days_map.get(dur_choice, 30)
                plan = plan_map.get(dur_choice, "VIP_PRO")
            
            bind_hw = input("\n🔒 ចង់ចាក់សោតាម HWID របស់ម៉ាស៊ីន Client ទេ?\n(ចុច Enter ដើម្បីអនុញ្ញាតប្រើបានគ្រប់ម៉ាស៊ីន ឬ Paste HWID របស់ Client): ").strip()
            hwid_val = bind_hw if bind_hw else None
            
            record = generate_license_key(client_name=client_name, duration_days=days, hwid=hwid_val, plan=plan)
            print_key_card(record)
            input("\nចុច Enter ដើម្បីបន្ត...")

        elif choice == "3":
            print("\n✍️ បង្កើត Custom Key ផ្ទាល់ខ្លួន (User-Defined Key / Password):")
            print(" (ឧទាហរណ៍៖ SAL-VIP-2026, SAL2026, VIP8888, KHMER-STUDIO)")
            custom_key = input("👉 បញ្ចូល Key ឬពាក្យសម្ងាត់ដែលបងចង់បាន: ").strip()
            if not custom_key:
                print("⚠️ មិនបានបញ្ចូល Key ទេ!")
                input("\nចុច Enter ដើម្បីបន្ត...")
                continue

            client_name = input("👤 ឈ្មោះ Client (ឧ. Sal / VIP_Customer): ").strip() or "VIP Client"
            
            print("\nកាលកំណត់សម្រាប់ Key នេះ:")
            print(" [1] ពេញមួយជីវិត (Lifetime VIP - គ្មានថ្ងៃផុតកំណត់)")
            print(" [2] វាយចំនួនថ្ងៃជាក់លាក់ (Custom Days ឧ. 7, 30, 90, 365...)")
            d_opt = input("👉 ជ្រើសរើស (1 ឬ 2): ").strip()
            if d_opt == "2":
                try:
                    days = int(input("👉 បញ្ចូលចំនួនថ្ងៃ: ").strip() or "30")
                except Exception:
                    days = 30
            else:
                days = 0

            bind_hw = input("\n🔒 ចង់ចាក់សោតាម HWID របស់ម៉ាស៊ីន Client ទេ?\n(ចុច Enter ដើម្បីប្រើបានគ្រប់ម៉ាស៊ីន ឬ Paste HWID): ").strip()
            hwid_val = bind_hw if bind_hw else None

            plan_name = f"CUSTOM_{days}D" if days > 0 else "CUSTOM_LIFETIME"
            rec = register_custom_key(custom_key=custom_key, client_name=client_name, duration_days=days, hwid=hwid_val, plan=plan_name)
            print_key_card(rec)
            input("\nចុច Enter ដើម្បីបន្ត...")

        elif choice == "4":
            print("\n🚫 បញ្ឈប់ / Block Key របស់ User (Revoke / Ban Key):")
            key_to_ban = input("👉 បញ្ចូល Key ដែលបងចង់ Block មិនឱ្យប្រើ: ").strip()
            if not key_to_ban:
                print("⚠️ មិនបានបញ្ចូល Key ទេ!")
                input("\nចុច Enter ដើម្បីបន្ត...")
                continue
            
            confirm = input(f"⚠️ តើបងប្រាកដទេថាចង់បញ្ឈប់/Block Key '{key_to_ban}'? (y/n): ").strip().lower()
            if confirm in ('y', 'yes', 'បាទ', 'ចាស'):
                ok, msg = revoke_license_key(key_to_ban, reason="Admin manual revoke")
                print(f"\n{msg}")
            else:
                print("🚫 បានបោះបង់ប្រតិបត្តិការ។")
            input("\nចុច Enter ដើម្បីបន្ត...")

        elif choice == "5":
            print("\n♻️ ដោះសោ / Unban Key (Restore Key):")
            key_to_unban = input("👉 បញ្ចូល Key ដែលចង់ Unblock ឱ្យដំណើរការវិញ: ").strip()
            if not key_to_unban:
                print("⚠️ មិនបានបញ្ចូល Key ទេ!")
                input("\nចុច Enter ដើម្បីបន្ត...")
                continue
            ok, msg = unrevoke_license_key(key_to_unban)
            print(f"\n{msg}")
            input("\nចុច Enter ដើម្បីបន្ត...")

        elif choice == "6":
            current_status = is_license_required()
            print(f"\n⚙️ ស្ថានភាពបច្ចុប្បន្ន៖ {'🟢 កំពុងទាមទារ License Key (ON)' if current_status else '🟡 កំពុងបើក Free Mode (OFF - មិនបាច់វាយ Key)'}")
            print(" [1] បើកការទាមទារ Key (User ត្រូវតែមាន Key ទើបប្រើបាន)")
            print(" [2] បិទការទាមទារ Key (Free Mode - អ្នកណាក៏បើកប្រើបានភ្លាមៗ)")
            toggle_choice = input("👉 ជ្រើសរើស (1 ឬ 2): ").strip()
            if toggle_choice == "1":
                set_license_required(True)
                print("✅ បានបើកការទាមទារ License Key (User ត្រូវវាយ Key ទើបប្រើបាន)")
            elif toggle_choice == "2":
                set_license_required(False)
                print("🎉 បានបើក Free Mode (User មិនបាច់វាយ Key ទេ បើកមកប្រើបានភ្លាមៗ)")
            input("\nចុច Enter ដើម្បីបន្ត...")

        elif choice == "7":
            if ADMIN_HISTORY_FILE.exists():
                with open(ADMIN_HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
                print(f"\n📜 បញ្ជី License Keys ទាំងអស់ ({len(history)} Keys):")
                print("-" * 65)
                for idx, k in enumerate(history, 1):
                    status_badge = "🔴 REVOKED" if k.get('status') == 'REVOKED' else "🟢 ACTIVE"
                    print(f"{idx}. [{status_badge}] {k.get('license_key')} | {k.get('client_name')} | Plan: {k.get('plan')} | Expiry: {k.get('expires_at')} | HWID: {k.get('bound_hwid')}")
                print("-" * 65)
            else:
                print("\n⚠️ មិនទាន់មាន Key ណាមួយត្រូវបានបង្កើតនៅឡើយទេ។")
            input("\nចុច Enter ដើម្បីបន្ត...")

        elif choice == "8":
            test_key = input("\n🔍 បញ្ចូល License Key ដែលចង់ Check: ").strip()
            valid, msg, record = verify_license_key(test_key)
            print(f"\nResult: {msg}")
            if valid:
                print(f"Client: {record.get('client_name')}, Plan: {record.get('plan')}, Expiry: {record.get('expires_at')}")
            input("\nចុច Enter ដើម្បីបន្ត...")

        elif choice == "9":
            name = input("\n👤 ឈ្មោះ Client: ").strip() or "User_Lifetime"
            rec = generate_license_key(client_name=name, duration_days=0, plan="VIP_LIFETIME")
            print_key_card(rec)
            input("\nចុច Enter ដើម្បីបន្ត...")

        elif choice.upper() in ("S", "SYNC"):
            print("\n🔄 កំពុង Sync Key ទាំងអស់ទៅកាន់ Online Registry...")
            keys = sync_online_keys()
            print(f"✅ បាន Sync Key សរុប {len(keys)} Keys ទៅកាន់ data/license_keys_online.json និង dist/ រួចរាល់!")
            input("\nចុច Enter ដើម្បីបន្ត...")

        elif choice in ("0", "exit", "quit"):
            print("\n👋 អរគុណ! ចាកចេញពី Admin Key Generator។\n")
            break

if __name__ == "__main__":
    interactive_menu()
