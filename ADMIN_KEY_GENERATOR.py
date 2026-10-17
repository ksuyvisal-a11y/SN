"""
===========================================================================
  🔐 SN STUDIO - ADMIN KEY GENERATOR & LICENSE MANAGER
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
    extend_license_key,
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
        try:
            import logging
            from admin_dashboard import admin_app
            log = logging.getLogger('werkzeug')
            log.setLevel(logging.ERROR)
            admin_app.run(host="127.0.0.1", port=ADMIN_PORT, debug=False, use_reloader=False)
        except Exception:
            pass
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
    lic_mode = "🟢 ON (Key Required)" if is_license_required() else "🟡 OFF (Free Mode - No Key Required)"
    server_status = f"🟢 Running ({ADMIN_URL})" if is_server_running() else "🟡 Starting..."
    print("\n" + "=" * 65)
    print(" 👑 SN STUDIO - ADMIN KEY GENERATOR (KEY MANAGEMENT SYSTEM)")
    print("=" * 65)
    print(f" 💻 Admin Machine HWID: {get_machine_hwid()}")
    print(f" 🛡️  License Gate Mode:  {lic_mode}")
    print(f" 🌐 Admin Dashboard:    {server_status}")
    print("=" * 65)

def print_key_card(record):
    client = record.get('client_name') or 'អតិថិជនកិត្តិយស'
    key = record.get('license_key', '')
    plan = record.get('plan') or 'PRO Lifetime'
    expiry = record.get('expires_at') or 'LIFETIME (ប្រើប្រាស់រហូត)'
    hwid = record.get('bound_hwid') or 'កុំព្យូទ័រណាក៏បាន (Any Machine)'
    if hwid in ['ANY', '*']:
        hwid = 'កុំព្យូទ័រណាក៏បាន (Any Machine)'

    delivery_msg = (
        f"\n=======================================================\n"
        f" 🎬 SN STUDIO - VIP LICENSE KEY\n"
        f"=======================================================\n"
        f" 👤 អតិថិជន (Client): {client}\n"
        f" 🔑 លេខកូដ (Key):     {key}\n"
        f" 📦 កញ្ចប់ (Plan):     {plan}\n"
        f" ⏳ សុពលភាព (Expiry): {expiry}\n"
        f" 🔒 ម៉ាស៊ីន (HWID):    {hwid}\n"
        f"-------------------------------------------------------\n"
        f" 📖 មគ្គុទ្ទេសក៍ណែនាំរហ័ស:\n"
        f" ១. បើកកម្មវិធី SN TOOL នៅលើកុំព្យូទ័រ\n"
        f" ២. Paste លេខ License Key ខាងលើ រួចចុច Activate License\n"
        f" ៣. ចូលប្រើ Downloader & AI Studio បានភ្លាមៗ ១០០%!\n"
        f"======================================================="
    )
    print(delivery_msg)
    copy_to_clipboard(key)
    print(" (✨ Key copied to Clipboard automatically!)")

def interactive_menu():
    ensure_server_running()
    while True:
        try:
            print_header()
            print(" 🌐 SECTION 1: WEB ADMIN DASHBOARD (BROWSER DASHBOARD)")
            print(" [1] Open Admin Dashboard (http://127.0.0.1:8888/admin)")
            print("-" * 65)
            print(" 🔑 SECTION 2: GENERATE KEY (KEY GENERATION)")
            print(" [2] Generate New License Key (Duration: 30d, 90d, 1y, Lifetime)")
            print(" [3] Generate Custom Key Code (e.g. SAL-2026)")
            print(" [9] Quick Lifetime Key (Permanent Key)")
            print("-" * 65)
            print(" 👥 SECTION 3: CUSTOMER MANAGEMENT & BLOCK USER")
            print(" [4] Block / Revoke User Key (Revoke / Ban Key)")
            print(" [5] Unban Key (Restore / Reactivate Key)")
            print(" [E] 📡 Extend / Renew Key Remotely (បន្តសុពលភាព Key ពីចម្ងាយ)")
            print(" [7] View All Keys History")
            print(" [8] Verify License Key")
            print("-" * 65)
            print(" ⚙️ SECTION 4: GATE & SYSTEM SETTINGS")
            print(" [6] Toggle Free Mode vs Require Key")
            print(" [S] 🔄 Sync & Export Online Keys")
            print(" [0] Exit")
            print("=" * 65)

            choice = input("👉 Select option (0-9 or S): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n⚠️ Interrupted. To exit, choose 0.")
            time.sleep(1)
            continue

        if choice == "1":
            import webbrowser
            print("\n⏳ Checking and starting Admin Server (Port 8888)...")
            ready = ensure_server_running(timeout=6.0)
            url = ADMIN_URL
            if ready:
                print(f"🌐 Admin Server ready! Opening Dashboard in browser ({url})...")
            else:
                print(f"⚠️ Admin Server starting slowly, attempting to open: {url}")
            try:
                webbrowser.open(url)
            except Exception:
                pass
            print(f"✅ If browser does not open automatically, visit: {url}")
            input("\nPress Enter to continue...")

        elif choice == "2":
            client_name = input("\n👤 Enter Client/User Name (e.g. Sokha_FB): ").strip() or "Client"
            print("\nSelect Duration:")
            print(" [1] 30 Days (1 Month)")
            print(" [2] 90 Days (3 Months)")
            print(" [3] 365 Days (1 Year)")
            print(" [4] Lifetime (Permanent)")
            print(" [5] 3-Day Trial")
            print(" [6] Custom Days (e.g. 5, 14, 60, 180...)")
            
            dur_choice = input("👉 Select (1-6): ").strip()
            if dur_choice == "6":
                try:
                    custom_d = int(input("👉 Enter number of days (0 for Lifetime): ").strip() or "30")
                    days = custom_d
                    plan = f"{days}D" if days > 0 else "LIFETIME"
                except Exception:
                    days = 30
                    plan = "30D"
            else:
                days_map = {"1": 30, "2": 90, "3": 365, "4": 0, "5": 3}
                plan_map = {"1": "1M", "2": "3M", "3": "1Y", "4": "LIFETIME", "5": "TRIAL_3D"}
                days = days_map.get(dur_choice, 30)
                plan = plan_map.get(dur_choice, "PRO")
            
            bind_hw = input("\n🔒 Lock to Client Machine HWID?\n(Press Enter for Any Machine, or paste Client HWID): ").strip()
            hwid_val = bind_hw if bind_hw else None
            
            record = generate_license_key(client_name=client_name, duration_days=days, hwid=hwid_val, plan=plan)
            print_key_card(record)
            input("\nPress Enter to continue...")

        elif choice == "3":
            print("\n✍️ Create Custom Key (User-Defined Key / Password):")
            print(" (e.g.: SAL-2026, SAL888, VIP-STUDIO)")
            custom_key = input("👉 Enter desired Key code: ").strip()
            if not custom_key:
                print("⚠️ No Key entered!")
                input("\nPress Enter to continue...")
                continue

            client_name = input("👤 Client Name (e.g. Sal / Sokha): ").strip() or "Client"
            
            print("\nDuration for this Key:")
            print(" [1] Lifetime (Permanent - Never Expires)")
            print(" [2] Custom Days (e.g. 7, 30, 90, 365...)")
            d_opt = input("👉 Select (1 or 2): ").strip()
            if d_opt == "2":
                try:
                    days = int(input("👉 Enter number of days: ").strip() or "30")
                except Exception:
                    days = 30
            else:
                days = 0

            bind_hw = input("\n🔒 Lock to Client Machine HWID?\n(Press Enter for Any Machine, or paste HWID): ").strip()
            hwid_val = bind_hw if bind_hw else None

            plan_name = f"CUSTOM_{days}D" if days > 0 else "CUSTOM_LIFETIME"
            rec = register_custom_key(custom_key=custom_key, client_name=client_name, duration_days=days, hwid=hwid_val, plan=plan_name)
            print_key_card(rec)
            input("\nPress Enter to continue...")

        elif choice == "4":
            print("\n🚫 Block / Revoke User Key:")
            key_to_ban = input("👉 Enter Key to block: ").strip()
            if not key_to_ban:
                print("⚠️ No Key entered!")
                input("\nPress Enter to continue...")
                continue
            
            confirm = input(f"⚠️ Are you sure you want to block Key '{key_to_ban}'? (y/n): ").strip().lower()
            if confirm in ('y', 'yes'):
                ok, msg = revoke_license_key(key_to_ban, reason="Admin manual revoke")
                print(f"\n{msg}")
            else:
                print("🚫 Operation cancelled.")
            input("\nPress Enter to continue...")

        elif choice == "5":
            print("\n♻️ Unban / Restore Key:")
            key_to_unban = input("👉 Enter Key to unblock: ").strip()
            if not key_to_unban:
                print("⚠️ No Key entered!")
                input("\nPress Enter to continue...")
                continue
            ok, msg = unrevoke_license_key(key_to_unban)
            print(f"\n{msg}")
            input("\nPress Enter to continue...")

        elif choice.upper() == "E":
            print("\n📡 EXTEND / RENEW LICENSE KEY REMOTELY (បន្តសុពលភាព Key ពីចម្ងាយ):")
            target_key = input("👉 Enter Customer's License Key to extend: ").strip()
            if not target_key:
                print("⚠️ No Key entered!")
                input("\nPress Enter to continue...")
                continue

            print("\nSelect Extension Duration (ជ្រើសរើសរយៈពេលបន្ត):")
            print(" [1] +30 Days (១ ខែ)")
            print(" [2] +90 Days (៣ ខែ)")
            print(" [3] +365 Days (១ ឆ្នាំ)")
            print(" [4] 👑 Lifetime (អចិន្ត្រៃយ៍ / រហូត)")
            print(" [5] Custom Days (បញ្ចូលចំនួនថ្ងៃតាមចិត្ត)")
            dur_sel = input("👉 Select (1-5): ").strip()

            if dur_sel == "1":
                add_days = 30
                plan = "PRO 30D"
            elif dur_sel == "2":
                add_days = 90
                plan = "PRO 90D"
            elif dur_sel == "3":
                add_days = 365
                plan = "PRO 1Y"
            elif dur_sel == "4":
                add_days = 0
                plan = "LIFETIME"
            elif dur_sel == "5":
                try:
                    add_days = int(input("👉 Enter number of days (e.g. 15, 60, 180): ").strip())
                    plan = f"PRO {add_days}D"
                except Exception:
                    add_days = 30
                    plan = "PRO 30D"
            else:
                add_days = 30
                plan = "PRO 30D"

            ok, msg, rec = extend_license_key(target_key, additional_days=add_days, plan=plan)
            print(f"\n{msg}")
            if ok:
                print(f"👤 Client:  {rec.get('client_name')}")
                print(f"🔑 Key:     {rec.get('license_key')}")
                print(f"📦 Plan:    {rec.get('plan')}")
                print(f"⏳ Expiry:  {rec.get('expires_at')}")
                print("\n✨ Updated online registry successfully! When customer opens tool, it auto-renews OTA!")
            input("\nPress Enter to continue...")

        elif choice == "6":
            current_status = is_license_required()
            print(f"\n⚙️ Current Status: {'🟢 License Key Required (ON)' if current_status else '🟡 Free Mode (OFF - No Key Required)'}")
            print(" [1] Enable Key Requirement (Valid key required)")
            print(" [2] Disable Key Requirement (Free Mode - Open to all)")
            toggle_choice = input("👉 Select (1 or 2): ").strip()
            if toggle_choice == "1":
                set_license_required(True)
                print("✅ Enabled License Key Requirement (Key required)")
            elif toggle_choice == "2":
                set_license_required(False)
                print("🎉 Enabled Free Mode (No key required)")
            input("\nPress Enter to continue...")

        elif choice == "7":
            if ADMIN_HISTORY_FILE.exists():
                with open(ADMIN_HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
                print(f"\n📜 All License Keys ({len(history)} Keys):")
                print("-" * 65)
                for idx, k in enumerate(history, 1):
                    status_badge = "🔴 REVOKED" if k.get('status') == 'REVOKED' else "🟢 ACTIVE"
                    print(f"{idx}. [{status_badge}] {k.get('license_key')} | {k.get('client_name')} | Plan: {k.get('plan')} | Expiry: {k.get('expires_at')} | HWID: {k.get('bound_hwid')}")
                print("-" * 65)
            else:
                print("\n⚠️ No keys generated yet.")
            input("\nPress Enter to continue...")

        elif choice == "8":
            test_key = input("\n🔍 Enter License Key to check: ").strip()
            valid, msg, record = verify_license_key(test_key)
            print(f"\nResult: {msg}")
            if valid:
                print(f"Client: {record.get('client_name')}, Plan: {record.get('plan')}, Expiry: {record.get('expires_at')}")
            input("\nPress Enter to continue...")

        elif choice == "9":
            name = input("\n👤 Client Name: ").strip() or "User_Lifetime"
            rec = generate_license_key(client_name=name, duration_days=0, plan="LIFETIME")
            print_key_card(rec)
            input("\nPress Enter to continue...")

        elif choice.upper() in ("S", "SYNC"):
            print("\n🔄 Syncing keys to Online Registry...")
            keys = sync_online_keys()
            print(f"✅ Synced {len(keys)} keys to data/license_keys_online.json and dist/ successfully!")
            input("\nPress Enter to continue...")

        elif choice in ("0", "exit", "quit"):
            confirm = input("👉 Are you sure you want to exit? (y/n): ").strip().lower()
            if confirm in ('y', 'yes'):
                print("\n👋 Goodbye! Safely exited Admin Key Generator.\n")
                break
            else:
                continue

        else:
            print(f"\n⚠️ Invalid choice '{choice}'! Please select from list (0-9 or S).")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        interactive_menu()
    except Exception as e:
        print(f"\n⚠️ An error occurred: {e}")
        input("\nPress Enter to close...")
