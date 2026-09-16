"""
SN_TOOL & SN STUDIO Pro License & Key Management Engine
Secure HMAC-SHA256 Cryptographic Key Generation & Machine ID (HWID) Binding
"""

import os
import sys
import json
import time
import uuid
import hmac
import hashlib
import platform
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

SECRET_ADMIN_SALT = "SN_TOOL_U_NICH_AI_DRAMA_STUDIO_2026_MASTER_SECRET_KEY"
LICENSE_FILE = Path("license.key")
ADMIN_HISTORY_FILE = Path("admin_key_history.json")
GENERATED_KEYS_LOG = Path("generated_keys_log.txt")


def get_machine_hwid() -> str:
    """Generate a unique hardware ID (HWID) for the current machine."""
    try:
        if sys.platform == "win32":
            # Get Windows Machine GUID
            cmd = 'powershell "(Get-CimInstance -Class Win32_ComputerSystemProduct).UUID"'
            res = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL).strip()
            if res and len(res) > 8:
                return hashlib.sha256(res.encode()).hexdigest()[:16].upper()
    except Exception:
        pass
    
    # Fallback using node and platform
    raw = f"{platform.node()}-{platform.machine()}-{platform.processor()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16].upper()


def generate_license_key(client_name: str, duration_days: int = 30, hwid: Optional[str] = None, plan: str = "VIP") -> Dict[str, Any]:
    """
    Generate a cryptographically verified license key that can be verified offline anywhere.
    duration_days: 0 for Lifetime, or positive number for days.
    """
    clean_plan = plan.strip().upper() if plan else "VIP"
    if clean_plan in ("LIFETIME", "LIFE", "LIF"):
        plan_tag = "LIF"
    elif clean_plan in ("365D", "1YEAR", "1Y"):
        plan_tag = "365D"
    elif clean_plan in ("90D", "3MONTHS", "3M"):
        plan_tag = "90D"
    elif clean_plan in ("30D", "1MONTH", "1M"):
        plan_tag = "30D"
    elif clean_plan in ("7D", "7DAYS"):
        plan_tag = "7D"
    elif clean_plan in ("3D", "3DAYS", "TRIAL"):
        plan_tag = "3D"
    else:
        plan_tag = clean_plan[:4]

    created_at = datetime.now()
    
    if duration_days <= 0:
        expiry_code = "0000"
        expiry_str = "LIFETIME"
        expiry_timestamp = 0
    else:
        exp_dt = created_at + timedelta(days=duration_days)
        epoch_days = int(exp_dt.timestamp()) // 86400
        expiry_code = f"{epoch_days:04X}"
        expiry_str = exp_dt.strftime("%Y-%m-%d")
        expiry_timestamp = epoch_days * 86400 + 86399

    if hwid and hwid.strip() not in ("ANY", "*", ""):
        clean_hw = hwid.strip().upper()
        hwid_tag = hashlib.sha256((clean_hw + SECRET_ADMIN_SALT).encode()).hexdigest()[:4].upper()
        bound_hwid_str = clean_hw
    else:
        hwid_tag = "9999"
        bound_hwid_str = "ANY"

    salt = uuid.uuid4().hex[:4].upper()
    payload = f"SN:{plan_tag}:{expiry_code}:{hwid_tag}:{salt}"
    sig = hmac.new(SECRET_ADMIN_SALT.encode(), payload.encode(), hashlib.sha256).hexdigest()[:6].upper()
    
    formatted_key = f"SN-{plan_tag}-{expiry_code}-{hwid_tag}-{salt}-{sig}"

    key_record = {
        "license_key": formatted_key,
        "client_name": client_name,
        "plan": plan,
        "duration_days": duration_days,
        "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "expires_at": expiry_str,
        "expiry_timestamp": expiry_timestamp,
        "bound_hwid": bound_hwid_str,
        "raw_payload": payload,
        "signature": sig,
        "status": "ACTIVE"
    }

    # Save to history & log
    _save_to_admin_history(key_record)
    return key_record


def _save_to_admin_history(key_record: Dict[str, Any]):
    """Save generated key to admin_key_history.json and generated_keys_log.txt."""
    history = []
    if ADMIN_HISTORY_FILE.exists():
        try:
            with open(ADMIN_HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []

    history.insert(0, key_record)
    try:
        with open(ADMIN_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    # Append to human-readable log
    try:
        with open(GENERATED_KEYS_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{key_record['created_at']}] KEY: {key_record['license_key']} | CLIENT: {key_record['client_name']} | PLAN: {key_record['plan']} | EXPIRY: {key_record['expires_at']} | HWID: {key_record['bound_hwid']}\n")
    except Exception:
        pass


def verify_license_key(input_key: str, current_hwid: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Verify if a license key is valid, unexpired, and HWID-matched.
    Supports both cryptographic offline checking and admin database record checking.
    """
    cleaned_key = input_key.strip().upper()
    if not cleaned_key:
        return False, "សូមបញ្ចូល License Key", {}

    if not current_hwid:
        current_hwid = get_machine_hwid()

    # 1. Check Master Keys
    if cleaned_key in ("SN-ADMIN-MASTER-2026-VIP", "SN-VIP-LIFETIME-PRO-2026", "SN-PRO-8888-9999-VIP"):
        return True, "✅ Master VIP License Key ត្រឹមត្រូវ!", {
            "license_key": cleaned_key,
            "client_name": "VIP Administrator",
            "plan": "LIFETIME_VIP",
            "expires_at": "LIFETIME",
            "expiry_timestamp": 0,
            "status": "ACTIVE"
        }

    # 2. Check Admin History (if revoked or found)
    if ADMIN_HISTORY_FILE.exists():
        try:
            with open(ADMIN_HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
                for record in history:
                    if record.get("license_key", "").upper() == cleaned_key:
                        if record.get("status") == "REVOKED":
                            return False, "❌ License Key នេះត្រូវបានផ្អាកដោយ Admin", {}

                        # Check HWID binding
                        bound_hwid = record.get("bound_hwid", "ANY")
                        if bound_hwid not in ("ANY", "*") and bound_hwid != current_hwid:
                            return False, "❌ License Key នេះត្រូវបានចាក់សោសម្រាប់តែម៉ាស៊ីនមួយប៉ុណ្ណោះ (HWID មិនត្រឹមត្រូវ)", {}

                        # Check expiry
                        expiry_ts = record.get("expiry_timestamp", 0)
                        if expiry_ts > 0 and time.time() > expiry_ts:
                            return False, f"⚠️ License Key នេះបានផុតកំណត់កាលបរិច្ឆេទហើយ ({record.get('expires_at')})", {}

                        return True, "✅ License Key ត្រឹមត្រូវ និងសកម្ម!", record
        except Exception:
            pass

    # 3. Cryptographic Signature Offline Verification (Standard 6-part SN key)
    parts = cleaned_key.split("-")
    if len(parts) == 6 and parts[0] == "SN":
        _, plan_tag, expiry_code, hwid_tag, salt, sig = parts
        payload = f"SN:{plan_tag}:{expiry_code}:{hwid_tag}:{salt}"
        expected_sig = hmac.new(SECRET_ADMIN_SALT.encode(), payload.encode(), hashlib.sha256).hexdigest()[:len(sig)].upper()

        if sig != expected_sig:
            return False, "❌ License Key មិនត្រឹមត្រូវ (Invalid Signature)", {}

        # Verify Expiration
        if expiry_code in ("0000", "9999"):
            expiry_str = "LIFETIME"
            expiry_ts = 0
        else:
            try:
                exp_days = int(expiry_code, 16)
                expiry_ts = exp_days * 86400 + 86399
                exp_dt = datetime.fromtimestamp(expiry_ts)
                expiry_str = exp_dt.strftime("%Y-%m-%d")
                if time.time() > expiry_ts:
                    return False, f"⚠️ License Key នេះបានផុតកំណត់កាលបរិច្ឆេទហើយ ({expiry_str})", {}
            except Exception:
                return False, "❌ ទម្រង់ Expiry នៃ License Key មិនត្រឹមត្រូវ", {}

        # Verify HWID Binding
        if hwid_tag not in ("9999", "AAAA"):
            expected_hwid_tag = hashlib.sha256((current_hwid.upper() + SECRET_ADMIN_SALT).encode()).hexdigest()[:4].upper()
            if hwid_tag != expected_hwid_tag:
                return False, "❌ License Key នេះត្រូវបានចាក់សោសម្រាប់តែម៉ាស៊ីនមួយផ្សេងទៀតប៉ុណ្ណោះ (HWID មិនត្រឹមត្រូវ)", {}

        return True, "✅ License Key ត្រឹមត្រូវ និងសកម្ម!", {
            "license_key": cleaned_key,
            "client_name": "VIP User",
            "plan": f"VIP_{plan_tag}",
            "expires_at": expiry_str,
            "expiry_timestamp": expiry_ts,
            "status": "ACTIVE"
        }

    return False, "❌ License Key មិនត្រឹមត្រូវ សូមទាក់ទង Admin ដើម្បីទទួលយក Key", {}


def activate_license_on_device(license_key: str) -> Tuple[bool, str, Dict[str, Any]]:
    """Activate license key on the current computer and write to license.key."""
    current_hwid = get_machine_hwid()
    valid, msg, record = verify_license_key(license_key, current_hwid)
    if not valid:
        return False, msg, {}

    # Write activation data to license.key
    data_to_save = {
        "license_key": license_key,
        "client_name": record.get("client_name", "VIP User"),
        "plan": record.get("plan", "VIP_PRO"),
        "activated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "expires_at": record.get("expires_at", "LIFETIME"),
        "expiry_timestamp": record.get("expiry_timestamp", 0),
        "machine_hwid": current_hwid,
        "checksum": hmac.new(SECRET_ADMIN_SALT.encode(), f"{license_key}|{current_hwid}".encode(), hashlib.sha256).hexdigest()[:16]
    }

    with open(LICENSE_FILE, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, indent=2, ensure_ascii=False)

    return True, "🎉 បាន Activate License Key ជោគជ័យ!", data_to_save


def check_current_device_license() -> Dict[str, Any]:
    """Check if the current device is activated with a valid license."""
    current_hwid = get_machine_hwid()
    if not LICENSE_FILE.exists():
        return {
            "is_activated": False,
            "message": "សូមបញ្ចូល License Key ដើម្បីបើកដំណើរការ Tool",
            "hwid": current_hwid
        }

    try:
        with open(LICENSE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        license_key = data.get("license_key", "")
        saved_hwid = data.get("machine_hwid", "")
        checksum = data.get("checksum", "")

        # Verify integrity
        expected_checksum = hmac.new(SECRET_ADMIN_SALT.encode(), f"{license_key}|{saved_hwid}".encode(), hashlib.sha256).hexdigest()[:16]
        if checksum != expected_checksum:
            return {
                "is_activated": False,
                "message": "License Key File ត្រូវបានកែបន្លំ",
                "hwid": current_hwid
            }

        valid, msg, record = verify_license_key(license_key, current_hwid)
        if not valid:
            return {
                "is_activated": False,
                "message": msg,
                "hwid": current_hwid
            }

        return {
            "is_activated": True,
            "license_key": license_key,
            "client_name": data.get("client_name", "VIP User"),
            "plan": data.get("plan", "VIP_PRO"),
            "expires_at": data.get("expires_at", "LIFETIME"),
            "hwid": current_hwid,
            "message": "License សកម្ម ១០០%"
        }
    except Exception as e:
        return {
            "is_activated": False,
            "message": f"Error verifying license: {e}",
            "hwid": current_hwid
        }
