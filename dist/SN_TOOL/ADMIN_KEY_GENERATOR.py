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

from license_engine import generate_license_key, verify_license_key, get_machine_hwid, ADMIN_HISTORY_FILE, GENERATED_KEYS_LOG

def copy_to_clipboard(text: str):
    """Copy text to Windows clipboard."""
    try:
        if sys.platform == "win32":
            import subprocess
            subprocess.run("clip", input=text.encode("utf-8"), check=True)
    except Exception:
        pass

def print_header():
    print("\n" + "=" * 65)
    print(" 👑 SN STUDIO - ADMIN KEY GENERATOR (ប្រព័ន្ធគ្រប់គ្រង KEY ជូន USER)")
    print("=" * 65)
    print(f" 💻 Admin Machine HWID: {get_machine_hwid()}")
    print("=" * 65)

def print_key_card(record):
    msg = (
        f"\n=======================================================\n"
        f" 🎬 SN STUDIO - VIP LICENSE KEY\n"
        f"=======================================================\n"
        f" 👤 Client:  {record['client_name']}\n"
        f" 🔑 Key:     {record['license_key']}\n"
        f" 📦 Plan:    {record['plan']}\n"
        f" ⏳ Expiry:  {record['expires_at']}\n"
        f" 🔒 HWID:    {record['bound_hwid']}\n"
        f"=======================================================\n"
        f"👉 របៀបប្រើ៖ បើក SN STUDIO -> យក Key នេះ Paste ចូលរួចចុច Activate\n"
        f"======================================================="
    )
    print(msg)
    copy_to_clipboard(record['license_key'])
    print(" (✨ បាន Copy Key ចូល Clipboard ស្វ័យប្រវត្ត រួចជាស្រេច!)")

def interactive_menu():
    while True:
        print_header()
        print(" [1] 🔑 បង្កើត License Key ថ្មី (Custom Duration & Client Name)")
        print(" [2] 📜 មើលប្រវត្តិ Key ទាំងអស់ (View All Generated Keys)")
        print(" [3] 🔍 ត្រួតពិនិត្យ និង Verify License Key")
        print(" [4] ⚡ បង្កើត 1-Month VIP Key ភ្លាមៗ (Quick 30-Day Key)")
        print(" [5] 🌟 បង្កើត Lifetime Permanent Key ភ្លាមៗ (Quick Lifetime Key)")
        print(" [6] 🚪 ចាកចេញ (Exit)")
        print("-" * 65)
        
        choice = input("👉 សូមជ្រើសរើសជម្រើស (1-6): ").strip()

        if choice == "1":
            client_name = input("\n👤 បញ្ចូលឈ្មោះ Client/User (ឧ. Sokha_FB): ").strip() or "VIP_Client"
            print("\nជ្រើសរើសកាលកំណត់ (Duration):")
            print(" [1] 30 ថ្ងៃ (1 Month)")
            print(" [2] 90 ថ្ងៃ (3 Months)")
            print(" [3] 365 ថ្ងៃ (1 Year)")
            print(" [4] ពេញមួយជីវិត (Lifetime VIP)")
            print(" [5] Trial 3 ថ្ងៃ (3-Day Trial)")
            
            dur_choice = input("👉 ជ្រើសរើស (1-5): ").strip()
            days_map = {"1": 30, "2": 90, "3": 365, "4": 0, "5": 3}
            plan_map = {"1": "VIP_1M", "2": "VIP_3M", "3": "VIP_1Y", "4": "VIP_LIFETIME", "5": "TRIAL_3D"}
            
            days = days_map.get(dur_choice, 30)
            plan = plan_map.get(dur_choice, "VIP_PRO")
            
            bind_hw = input("\n🔒 ចង់ចាក់សោតាម HWID របស់ម៉ាស៊ីន Client ទេ?\n(ចុច Enter ដើម្បីអនុញ្ញាតប្រើបានគ្រប់ម៉ាស៊ីន ឬ Paste HWID របស់ Client): ").strip()
            hwid_val = bind_hw if bind_hw else None
            
            record = generate_license_key(client_name=client_name, duration_days=days, hwid=hwid_val, plan=plan)
            print_key_card(record)
            input("\nចុច Enter ដើម្បីបន្ត...")

        elif choice == "2":
            if ADMIN_HISTORY_FILE.exists():
                with open(ADMIN_HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
                print(f"\n📜 បញ្ជី License Keys ទាំងអស់ ({len(history)} Keys):")
                print("-" * 65)
                for idx, k in enumerate(history, 1):
                    print(f"{idx}. [{k.get('status', 'ACTIVE')}] {k['license_key']} | {k.get('client_name')} | Expiry: {k.get('expires_at')} | HWID: {k.get('bound_hwid')}")
                print("-" * 65)
            else:
                print("\n⚠️ មិនទាន់មាន Key ណាមួយត្រូវបានបង្កើតនៅឡើយទេ។")
            input("\nចុច Enter ដើម្បីបន្ត...")

        elif choice == "3":
            test_key = input("\n🔍 បញ្ចូល License Key ដែលចង់ Check: ").strip()
            valid, msg, record = verify_license_key(test_key)
            print(f"\nResult: {msg}")
            if valid:
                print(f"Client: {record.get('client_name')}, Plan: {record.get('plan')}, Expiry: {record.get('expires_at')}")
            input("\nចុច Enter ដើម្បីបន្ត...")

        elif choice == "4":
            name = input("\n👤 ឈ្មោះ Client: ").strip() or "User_1M"
            rec = generate_license_key(client_name=name, duration_days=30, plan="VIP_1M")
            print_key_card(rec)
            input("\nចុច Enter ដើម្បីបន្ត...")

        elif choice == "5":
            name = input("\n👤 ឈ្មោះ Client: ").strip() or "User_Lifetime"
            rec = generate_license_key(client_name=name, duration_days=0, plan="VIP_LIFETIME")
            print_key_card(rec)
            input("\nចុច Enter ដើម្បីបន្ត...")

        elif choice == "6":
            print("\n👋 អរគុណ! ចាកចេញពី Admin Key Generator។\n")
            break

if __name__ == "__main__":
    interactive_menu()
