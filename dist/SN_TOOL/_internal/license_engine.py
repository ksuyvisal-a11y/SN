"""
SN_TOOL & SN STUDIO Pro License & Key Management Engine
Secure HMAC-SHA256 Cryptographic Key Generation & Machine ID (HWID) Binding
"""

import os
import sys
import re
import json
import time
import uuid
import hmac
import hashlib
import platform
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

SECRET_ADMIN_SALT = "SN_TOOL_U_NICH_AI_DRAMA_STUDIO_2026_MASTER_SECRET_KEY"
LICENSE_FILE = Path("license.key")
ADMIN_HISTORY_FILE = Path("admin_key_history.json")
GENERATED_KEYS_LOG = Path("generated_keys_log.txt")
CUSTOM_KEYS_FILE = Path("custom_keys.json")
LICENSE_CONFIG_FILE = Path("license_config.json")
REVOKED_KEYS_FILE = Path("revoked_keys.json")
ONLINE_KEYS_LOCAL_FILE = Path("data/license_keys_online.json")


def resolve_file_path(relative_path: str) -> Path:
    """Resolve file path across dev root, frozen sys._MEIPASS, and distribution folders."""
    p = Path(relative_path)
    if p.exists():
        return p
    # Check _internal
    internal_p = Path("_internal") / relative_path
    if internal_p.exists():
        return internal_p
    # Check sys._MEIPASS if frozen
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        meipass_p = Path(sys._MEIPASS) / relative_path
        if meipass_p.exists():
            return meipass_p
    # Check next to executable
    try:
        exe_dir = Path(sys.executable).parent
        exe_p = exe_dir / relative_path
        if exe_p.exists():
            return exe_p
    except Exception:
        pass
    return p


# Built-in Master Keys that work permanently out of the box (100% Offline & Online)
DEFAULT_MASTER_KEYS: Dict[str, Dict[str, Any]] = {
    "SN-ADMIN-MASTER-2026": {"client_name": "Administrator", "plan": "LIFETIME"},
    "SN-ADMIN-MASTER-2026-VIP": {"client_name": "Administrator", "plan": "LIFETIME"},
    "SN-VIP-LIFETIME-PRO-2026": {"client_name": "Administrator", "plan": "LIFETIME"},
    "SN-PRO-8888-9999-VIP": {"client_name": "Administrator", "plan": "LIFETIME"},
    "SAL-VIP-2026": {"client_name": "Sal", "plan": "LIFETIME"},
    "SAL-VIP-888": {"client_name": "Khmer User", "plan": "LIFETIME"},
    "SAL-2026": {"client_name": "Sal", "plan": "LIFETIME"},
    "MYPASS888": {"client_name": "Customer", "plan": "LIFETIME"},
    "VIP-CAMBODIA-2026": {"client_name": "Cambodia User", "plan": "LIFETIME"},
    "VIP-PRO-2026": {"client_name": "Studio Pro", "plan": "LIFETIME"},
    "SN-STUDIO-PRO": {"client_name": "Studio Pro", "plan": "LIFETIME"},
    "SN-VIP-8888": {"client_name": "Member", "plan": "LIFETIME"},
    "VIP-STUDIO-2026": {"client_name": "Studio Member", "plan": "LIFETIME"},
    "SN-2026-PRO": {"client_name": "SN Pro", "plan": "LIFETIME"},
    "LIFETIME-VIP": {"client_name": "Lifetime User", "plan": "LIFETIME"},
    "VIP-DARA-2026": {"client_name": "Dara", "plan": "LIFETIME"},
    "SN-VIP": {"client_name": "Member", "plan": "LIFETIME"},
    "VIP2026": {"client_name": "Member", "plan": "LIFETIME"},
}


def is_license_required() -> bool:
    """Check if the system requires a license key or is in Free / Open Access mode."""
    cfg_p = resolve_file_path("license_config.json")
    if cfg_p.exists():
        try:
            with open(cfg_p, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                return bool(cfg.get("require_license", True))
        except Exception:
            pass
    return True


def set_license_required(required: bool) -> bool:
    """Turn license gate requirement ON or OFF."""
    cfg = {}
    if LICENSE_CONFIG_FILE.exists():
        try:
            with open(LICENSE_CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            cfg = {}
    cfg["require_license"] = bool(required)
    try:
        with open(LICENSE_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def register_custom_key(custom_key: str, client_name: str = "Client", duration_days: int = 0, hwid: Optional[str] = None, plan: str = "CUSTOM") -> Dict[str, Any]:
    """
    Register an arbitrary custom key/password created directly by the user.
    duration_days: 0 for Lifetime, or any positive number of days (e.g. 5, 10, 45, 60, etc.)
    """
    cleaned_key = custom_key.strip().upper()
    created_at = datetime.now()

    if duration_days <= 0:
        expiry_str = "LIFETIME"
        expiry_timestamp = 0
    else:
        exp_dt = created_at + timedelta(days=duration_days)
        expiry_str = exp_dt.strftime("%Y-%m-%d")
        epoch_days = int(exp_dt.timestamp()) // 86400
        expiry_timestamp = epoch_days * 86400 + 86399

    bound_hwid_str = hwid.strip().upper() if (hwid and hwid.strip() not in ("ANY", "*", "")) else "ANY"

    record = {
        "license_key": cleaned_key,
        "client_name": client_name or "Client",
        "plan": plan or "CUSTOM",
        "duration_days": duration_days,
        "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "expires_at": expiry_str,
        "expiry_timestamp": expiry_timestamp,
        "bound_hwid": bound_hwid_str,
        "raw_payload": f"CUSTOM:{cleaned_key}:{client_name}",
        "signature": "CUSTOM_ADMIN",
        "status": "ACTIVE"
    }

    # Save to custom_keys.json
    custom_keys = {}
    if CUSTOM_KEYS_FILE.exists():
        try:
            with open(CUSTOM_KEYS_FILE, "r", encoding="utf-8") as f:
                custom_keys = json.load(f)
        except Exception:
            custom_keys = {}

    custom_keys[cleaned_key] = record
    try:
        with open(CUSTOM_KEYS_FILE, "w", encoding="utf-8") as f:
            json.dump(custom_keys, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    # Save to history & log
    _save_to_admin_history(record)
    return record


def get_all_custom_keys() -> Dict[str, Any]:
    """Retrieve all custom keys defined by admin."""
    if CUSTOM_KEYS_FILE.exists():
        try:
            with open(CUSTOM_KEYS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def get_revoked_keys() -> List[str]:
    """Get list of all revoked / banned license keys."""
    for fn in ["revoked_keys.json", "data/revoked_keys.json"]:
        p = resolve_file_path(fn)
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return [k.strip().upper() for k in data]
                    elif isinstance(data, dict):
                        return [k.strip().upper() for k in data.get("revoked_keys", [])]
            except Exception:
                pass
    return []


def sync_online_keys() -> Dict[str, Any]:
    """
    Consolidate all valid keys (DEFAULT_MASTER_KEYS, custom keys, admin history)
    and export into data/license_keys_online.json, syncing to dist/SN_TOOL if present.
    """
    all_keys = {}

    # 1. Add Default Master Keys (Always active, universal ANY HWID)
    for mk, meta in DEFAULT_MASTER_KEYS.items():
        all_keys[mk] = {
            "license_key": mk,
            "client_name": meta.get("client_name", "Administrator"),
            "plan": meta.get("plan", "LIFETIME"),
            "duration_days": 0,
            "created_at": "2026-10-01 00:00:00",
            "expires_at": "LIFETIME",
            "expiry_timestamp": 0,
            "bound_hwid": "ANY",
            "status": "ACTIVE"
        }

    # 3. Add Custom Keys
    custom_p = resolve_file_path("custom_keys.json")
    if custom_p.exists():
        try:
            with open(custom_p, "r", encoding="utf-8") as f:
                ck = json.load(f)
                if isinstance(ck, dict):
                    for k, rec in ck.items():
                        all_keys[k.strip().upper()] = rec
        except Exception:
            pass

    # 4. Add Admin History Records
    history_p = resolve_file_path("admin_key_history.json")
    if history_p.exists():
        try:
            with open(history_p, "r", encoding="utf-8") as f:
                history = json.load(f)
                if isinstance(history, list):
                    for rec in history:
                        k = rec.get("license_key", "").strip().upper()
                        if k:
                            all_keys[k] = rec
        except Exception:
            pass

    # 5. Apply revocation overrides & ensure master keys are ANY hwid
    revoked = set(get_revoked_keys())
    for k, rec in all_keys.items():
        if k in revoked:
            rec["status"] = "REVOKED"
        elif rec.get("status") != "REVOKED":
            rec["status"] = "ACTIVE"
        if k in DEFAULT_MASTER_KEYS or k == "SN-ADMIN-MASTER-2026-VIP":
            rec["bound_hwid"] = "ANY"

    # 6. Save to data/license_keys_online.json and distribution folders
    target_paths = [
        Path("data/license_keys_online.json"),
        Path("dist/SN_TOOL/data/license_keys_online.json"),
        Path("dist/SN_TOOL/_internal/data/license_keys_online.json"),
    ]
    for tp in target_paths:
        try:
            if tp.parent.exists() or tp == target_paths[0]:
                tp.parent.mkdir(parents=True, exist_ok=True)
                with open(tp, "w", encoding="utf-8") as f:
                    json.dump(all_keys, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    # 7. Also sync revoked_keys.json across root, data/, and dist/
    revoked_paths = [
        Path("data/revoked_keys.json"),
        Path("revoked_keys.json"),
        Path("dist/SN_TOOL/data/revoked_keys.json"),
        Path("dist/SN_TOOL/_internal/data/revoked_keys.json"),
    ]
    rev_payload = {
        "revoked_keys": list(revoked),
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    for rp in revoked_paths:
        try:
            if rp.parent.exists() or rp == revoked_paths[0]:
                rp.parent.mkdir(parents=True, exist_ok=True)
                with open(rp, "w", encoding="utf-8") as f:
                    json.dump(rev_payload, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    return all_keys


def _cache_online_key_locally(cleaned_key: str, record: Dict[str, Any]):
    """Cache online-fetched key into local database for offline resilience."""
    try:
        p = resolve_file_path("data/license_keys_online.json")
        p.parent.mkdir(parents=True, exist_ok=True)
        cached = {}
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    cached = json.load(f)
            except Exception:
                cached = {}
        cached[cleaned_key] = record
        with open(p, "w", encoding="utf-8") as f:
            json.dump(cached, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def check_key_online(cleaned_key: str, current_hwid: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Check if a key is registered in online cloud registry (GitHub) or local online database.
    Returns (is_valid, message, record_dict).
    """
    cfg_file = resolve_file_path("license_config.json")
    online_url = "https://raw.githubusercontent.com/ksuyvisal-a11y/SN/main/data/license_keys_online.json"
    if cfg_file.exists():
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                online_url = cfg.get("online_keys_url", online_url)
        except Exception:
            pass

    record = None
    source = "offline_db"

    # 1. Try remote Cloud / GitHub registry first (quick 2.5s timeout)
    if online_url:
        try:
            import urllib.request
            req = urllib.request.Request(
                online_url,
                headers={"User-Agent": "SN_TOOL_License_Client", "Cache-Control": "no-cache"}
            )
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                if resp.status == 200:
                    cloud_keys = json.loads(resp.read().decode("utf-8"))
                    if isinstance(cloud_keys, dict) and cleaned_key in cloud_keys:
                        record = cloud_keys[cleaned_key]
                        source = "online_cloud"
                        _cache_online_key_locally(cleaned_key, record)
        except Exception:
            pass

    # 2. Fallback to local online database if remote didn't find it or was unreachable
    if not record:
        local_online_path = resolve_file_path("data/license_keys_online.json")
        if local_online_path.exists():
            try:
                with open(local_online_path, "r", encoding="utf-8") as f:
                    local_dict = json.load(f)
                if isinstance(local_dict, dict) and cleaned_key in local_dict:
                    record = local_dict[cleaned_key]
                    source = "local_db"
            except Exception:
                pass

    if not record:
        return False, "", {}

    # Validate status
    if record.get("status") == "REVOKED":
        return False, "❌ License Key នេះត្រូវបាន Admin ផ្អាកការប្រើប្រាស់ (Revoked/Suspended)", {}

    # Validate HWID binding
    bound_hwid = str(record.get("bound_hwid", "ANY")).strip().upper()
    if bound_hwid not in ("ANY", "*", "", "NONE") and bound_hwid != current_hwid:
        return False, "❌ License Key នេះត្រូវបានចាក់សោសម្រាប់តែម៉ាស៊ីនមួយប៉ុណ្ណោះ (HWID មិនត្រឹមត្រូវ)", {}

    # Validate Expiration
    expiry_ts = record.get("expiry_timestamp", 0)
    if expiry_ts > 0 and time.time() > expiry_ts:
        return False, f"⚠️ License Key នេះបានផុតកំណត់កាលបរិច្ឆេទហើយ ({record.get('expires_at')})", {}

    status_tag = "Online Cloud" if source == "online_cloud" else "Verified"
    return True, f"✅ License Key {status_tag} ត្រឹមត្រូវ និងសកម្ម!", record


def revoke_license_key(target_key: str, reason: str = "Banned by Admin") -> Tuple[bool, str]:
    """Revoke/Ban a license key so the user cannot use the tool anymore."""
    cleaned = target_key.strip().upper()
    if not cleaned:
        return False, "សូមបញ្ចូល Key ដែលត្រូវ Revoke"

    revoked_list = get_revoked_keys()
    if cleaned not in revoked_list:
        revoked_list.append(cleaned)
        try:
            with open(REVOKED_KEYS_FILE, "w", encoding="utf-8") as f:
                json.dump({"revoked_keys": revoked_list, "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            return False, f"Failed saving revoked_keys.json: {e}"

    # Also update admin_key_history.json
    if ADMIN_HISTORY_FILE.exists():
        try:
            with open(ADMIN_HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
            for r in history:
                if r.get("license_key", "").upper() == cleaned:
                    r["status"] = "REVOKED"
                    r["revoked_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    r["revoke_reason"] = reason
            with open(ADMIN_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    # Also update custom_keys.json
    if CUSTOM_KEYS_FILE.exists():
        try:
            with open(CUSTOM_KEYS_FILE, "r", encoding="utf-8") as f:
                ck = json.load(f)
            if cleaned in ck:
                ck[cleaned]["status"] = "REVOKED"
                ck[cleaned]["revoked_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(CUSTOM_KEYS_FILE, "w", encoding="utf-8") as f:
                    json.dump(ck, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    # If the current machine is using this revoked key, delete license.key
    if LICENSE_FILE.exists():
        try:
            with open(LICENSE_FILE, "r", encoding="utf-8") as f:
                current_lic = json.load(f)
            if current_lic.get("license_key", "").upper() == cleaned:
                LICENSE_FILE.unlink(missing_ok=True)
        except Exception:
            pass

    try:
        sync_online_keys()
    except Exception:
        pass

    return True, f"🚫 បាន Revoke / Ban Key {cleaned} ជោគជ័យ!"


def unrevoke_license_key(target_key: str) -> Tuple[bool, str]:
    """Unban / Restore a revoked license key."""
    cleaned = target_key.strip().upper()
    revoked_list = get_revoked_keys()
    if cleaned in revoked_list:
        revoked_list.remove(cleaned)
        try:
            with open(REVOKED_KEYS_FILE, "w", encoding="utf-8") as f:
                json.dump({"revoked_keys": revoked_list, "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    # Restore in admin_key_history.json
    if ADMIN_HISTORY_FILE.exists():
        try:
            with open(ADMIN_HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
            for r in history:
                if r.get("license_key", "").upper() == cleaned:
                    r["status"] = "ACTIVE"
            with open(ADMIN_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    # Restore in custom_keys.json
    if CUSTOM_KEYS_FILE.exists():
        try:
            with open(CUSTOM_KEYS_FILE, "r", encoding="utf-8") as f:
                ck = json.load(f)
            if cleaned in ck:
                ck[cleaned]["status"] = "ACTIVE"
                with open(CUSTOM_KEYS_FILE, "w", encoding="utf-8") as f:
                    json.dump(ck, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    try:
        sync_online_keys()
    except Exception:
        pass

    return True, f"✅ បានដោះសោ (Unban) Key {cleaned} ឱ្យដំណើរការឡើងវិញជោគជ័យ!"


def delete_license_key_record(target_key: str) -> Tuple[bool, str]:
    """Delete a key record completely from history, custom keys, and revocations."""
    cleaned = target_key.strip().upper()
    if not cleaned:
        return False, "សូមជ្រើសរើស Key ដែលត្រូវលុប"

    # Remove from admin_key_history.json
    if ADMIN_HISTORY_FILE.exists():
        try:
            with open(ADMIN_HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
            history = [r for r in history if r.get("license_key", "").upper() != cleaned]
            with open(ADMIN_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    # Remove from custom_keys.json
    if CUSTOM_KEYS_FILE.exists():
        try:
            with open(CUSTOM_KEYS_FILE, "r", encoding="utf-8") as f:
                ck = json.load(f)
            if cleaned in ck:
                del ck[cleaned]
                with open(CUSTOM_KEYS_FILE, "w", encoding="utf-8") as f:
                    json.dump(ck, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    # Remove from revoked_keys.json if present
    revoked = get_revoked_keys()
    if cleaned in revoked:
        revoked.remove(cleaned)
        try:
            with open(REVOKED_KEYS_FILE, "w", encoding="utf-8") as f:
                json.dump({"revoked_keys": revoked, "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    # Remove from generated_keys_log.txt if present
    if GENERATED_KEYS_LOG.exists():
        try:
            with open(GENERATED_KEYS_LOG, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            new_lines = [l for l in lines if f"KEY: {cleaned}" not in l and f"KEY:{cleaned}" not in l]
            with open(GENERATED_KEYS_LOG, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
        except Exception:
            pass

    try:
        sync_online_keys()
    except Exception:
        pass

    return True, f"🗑️ បានលុប Key {cleaned} ចេញពីបញ្ជីជោគជ័យ!"


def clear_all_admin_keys() -> Tuple[bool, str]:
    """
    Purge all customer keys, reset admin history, custom keys, and log.
    Built-in Master keys (DEFAULT_MASTER_KEYS) are retained.
    """
    try:
        with open(ADMIN_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    try:
        with open(CUSTOM_KEYS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    try:
        with open(GENERATED_KEYS_LOG, "w", encoding="utf-8") as f:
            f.write("# SN STUDIO - License Key Log\n")
    except Exception:
        pass

    # Also clean dist versions if they exist
    for dist_dir in [Path("dist/SN_TOOL"), Path("dist/SN_TOOL/_internal")]:
        try:
            ck = dist_dir / "custom_keys.json"
            if ck.exists():
                with open(ck, "w", encoding="utf-8") as f:
                    json.dump({}, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    try:
        sync_online_keys()
    except Exception:
        pass

    return True, "✅ បានជម្រះបញ្ជីឈ្មោះ Customer និង Keys ទាំងអស់ជោគជ័យ! បញ្ជី Key ឥឡូវនៅសល់ 0 ត្រៀមសម្រាប់ដាក់លក់ជូន User ថ្មី។"


def check_remote_revocation_online(cleaned_key: str, current_hwid: str) -> Optional[str]:
    """Check online remote blacklist endpoint if configured (quick 1.5s timeout)."""
    cfg_p = resolve_file_path("license_config.json")
    if not cfg_p.exists():
        return None
    try:
        with open(cfg_p, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        remote_url = cfg.get("remote_revocation_url")
        if not remote_url:
            return None
        import urllib.request
        req = urllib.request.Request(remote_url, headers={"User-Agent": "SN_Studio_License_Agent", "Cache-Control": "no-cache"})
        with urllib.request.urlopen(req, timeout=1.5) as res:
            if res.status == 200:
                data = json.loads(res.read().decode('utf-8'))
                remote_revoked = [k.strip().upper() for k in data.get("revoked_keys", [])]
                remote_hwids = [h.strip().upper() for h in data.get("revoked_hwids", [])]
                if cleaned_key in remote_revoked:
                    return "❌ License Key នេះត្រូវបាន Admin បញ្ឈប់ពីចម្ងាយ (Remote Revoked by Admin)"
                if current_hwid in remote_hwids:
                    return "❌ ម៉ាស៊ីននេះត្រូវបាន Admin បញ្ឈប់ពីចម្ងាយ (Device Banned by Admin)"
    except Exception:
        pass
    return None


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


def generate_license_key(client_name: str, duration_days: int = 30, hwid: Optional[str] = None, plan: str = "PRO") -> Dict[str, Any]:
    """
    Generate a cryptographically verified license key that can be verified offline anywhere.
    duration_days: 0 for Lifetime, or positive number for days.
    """
    clean_plan = plan.strip().upper() if plan else "PRO"
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

    try:
        sync_online_keys()
    except Exception:
        pass


def calculate_key_live_status(key_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate dynamic live status, remaining days, expiring-soon alerts, and usage metadata.
    """
    rec = dict(key_record)
    cleaned_key = rec.get("license_key", "").strip().upper()
    revoked_list = get_revoked_keys()

    # 1. Check Revoked Status
    if rec.get("status") == "REVOKED" or cleaned_key in revoked_list:
        rec["live_status"] = "REVOKED"
        rec["days_remaining"] = 0
        rec["is_expired"] = False
        rec["is_expiring_soon"] = False
        rec["badge_class"] = "stat-pill-red"
        rec["badge_label"] = "REVOKED"
        rec["status_kh"] = "🚫 បានផ្អាក (Revoked)"
        rec["remaining_text"] = "ត្រូវបានផ្អាកដោយ Admin"
        rec["last_active"] = rec.get("last_active") or rec.get("activated_at") or "មិនទាន់ចូលប្រើ"
        rec["use_count"] = rec.get("use_count", 0)
        return rec

    # 2. Check Expiry
    expires_at = str(rec.get("expires_at", "")).strip().upper()
    expiry_ts = rec.get("expiry_timestamp", 0)

    if expires_at in ("LIFETIME", "0000", "NEVER", "") or expiry_ts == 0:
        rec["live_status"] = "LIFETIME"
        rec["days_remaining"] = 99999
        rec["is_expired"] = False
        rec["is_expiring_soon"] = False
        rec["badge_class"] = "stat-pill-purple"
        rec["badge_label"] = "LIFETIME"
        rec["status_kh"] = "👑 មួយជីវិត (Lifetime)"
        rec["remaining_text"] = "ប្រើប្រាស់បានរហូត (Lifetime)"
        rec["last_active"] = rec.get("last_active") or rec.get("activated_at") or "មិនទាន់ចូលប្រើ"
        rec["use_count"] = rec.get("use_count", 0)
        return rec

    # Try parsing expiration date
    exp_date = None
    try:
        if expiry_ts and expiry_ts > 0:
            exp_date = datetime.fromtimestamp(expiry_ts)
        else:
            exp_date = datetime.strptime(expires_at, "%Y-%m-%d")
    except Exception:
        try:
            exp_date = datetime.strptime(expires_at.split()[0], "%Y-%m-%d")
        except Exception:
            pass

    if not exp_date:
        rec["live_status"] = "ACTIVE"
        rec["days_remaining"] = 30
        rec["is_expired"] = False
        rec["is_expiring_soon"] = False
        rec["badge_class"] = "stat-pill-green"
        rec["badge_label"] = "ACTIVE"
        rec["status_kh"] = "🟢 សកម្ម (Active)"
        rec["remaining_text"] = expires_at
        rec["last_active"] = rec.get("last_active") or rec.get("activated_at") or "មិនទាន់ចូលប្រើ"
        rec["use_count"] = rec.get("use_count", 0)
        return rec

    now = datetime.now()
    days_left = (exp_date.date() - now.date()).days

    if days_left < 0:
        rec["live_status"] = "EXPIRED"
        rec["days_remaining"] = days_left
        rec["is_expired"] = True
        rec["is_expiring_soon"] = False
        rec["badge_class"] = "stat-pill-red"
        rec["badge_label"] = "EXPIRED"
        rec["status_kh"] = f"🔴 ផុតកំណត់ ({abs(days_left)} ថ្ងៃមុន)"
        rec["remaining_text"] = f"ផុតកំណត់កាលពី {abs(days_left)} ថ្ងៃមុន"
    elif days_left <= 7:
        rec["live_status"] = "EXPIRING_SOON"
        rec["days_remaining"] = days_left
        rec["is_expired"] = False
        rec["is_expiring_soon"] = True
        rec["badge_class"] = "stat-pill-amber"
        rec["badge_label"] = f"EXPIRING ({days_left}D)"
        rec["status_kh"] = f"⚠️ ជិតផុតកំណត់ (សល់ {days_left} ថ្ងៃ)"
        rec["remaining_text"] = f"នៅសល់ {days_left} ថ្ងៃទៀតផុតកំណត់"
    else:
        rec["live_status"] = "ACTIVE"
        rec["days_remaining"] = days_left
        rec["is_expired"] = False
        rec["is_expiring_soon"] = False
        rec["badge_class"] = "stat-pill-green"
        rec["badge_label"] = "ACTIVE"
        rec["status_kh"] = f"🟢 សកម្ម (សល់ {days_left} ថ្ងៃ)"
        rec["remaining_text"] = f"នៅសល់ {days_left} ថ្ងៃ"

    rec["last_active"] = rec.get("last_active") or rec.get("activated_at") or "មិនទាន់ចូលប្រើ"
    rec["use_count"] = rec.get("use_count", 0)
    return rec


def sync_and_load_admin_history() -> List[Dict[str, Any]]:
    """
    Load admin key history, sync missing items from generated_keys_log.txt and custom_keys.json,
    and compute live dynamic expiry status & remaining days.
    """
    history: List[Dict[str, Any]] = []
    seen_keys = set()

    if ADMIN_HISTORY_FILE.exists():
        try:
            with open(ADMIN_HISTORY_FILE, "r", encoding="utf-8") as f:
                raw_hist = json.load(f)
                if isinstance(raw_hist, list):
                    for r in raw_hist:
                        k = r.get("license_key", "").strip().upper()
                        if k and k not in seen_keys:
                            history.append(r)
                            seen_keys.add(k)
        except Exception:
            history = []

    # Also sync from custom_keys.json
    if CUSTOM_KEYS_FILE.exists():
        try:
            with open(CUSTOM_KEYS_FILE, "r", encoding="utf-8") as f:
                ck_dict = json.load(f)
                if isinstance(ck_dict, dict):
                    for k, rec in ck_dict.items():
                        cleaned_k = k.strip().upper()
                        if cleaned_k and cleaned_k not in seen_keys:
                            history.append(rec)
                            seen_keys.add(cleaned_k)
        except Exception:
            pass

    # Save consolidated back to ADMIN_HISTORY_FILE
    try:
        with open(ADMIN_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    # Enrich each record with live calculations
    enriched = [calculate_key_live_status(r) for r in history]
    return enriched


def touch_license_activity(license_key: str, hwid: Optional[str] = None):
    """Update last active timestamp and usage count when client uses the application."""
    if not license_key:
        return
    cleaned_key = license_key.strip().upper()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Update in ADMIN_HISTORY_FILE
    if ADMIN_HISTORY_FILE.exists():
        try:
            with open(ADMIN_HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
            changed = False
            for r in history:
                if r.get("license_key", "").strip().upper() == cleaned_key:
                    r["last_active"] = now_str
                    r["use_count"] = int(r.get("use_count", 0)) + 1
                    if hwid and hwid not in ("ANY", ""):
                        r["last_active_hwid"] = hwid
                    changed = True
                    break
            if changed:
                with open(ADMIN_HISTORY_FILE, "w", encoding="utf-8") as f:
                    json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception:
            pass


def verify_license_key(input_key: str, current_hwid: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Verify if a license key is valid, unexpired, and HWID-matched.
    Supports Online Cloud Verification, Master Keys, Admin/Custom records, and Offline Cryptographic Checking.
    """
    cleaned_key = input_key.strip().upper()
    if not cleaned_key:
        return False, "សូមបញ្ចូល License Key", {}

    if not current_hwid:
        current_hwid = get_machine_hwid()

    # 0. Check Blacklist / Revocations (Local & Remote Kill Switch)
    if cleaned_key in get_revoked_keys():
        return False, "❌ License Key នេះត្រូវបាន Admin បញ្ឈប់/ផ្អាកការប្រើប្រាស់ (Revoked/Suspended by Admin)", {}

    remote_msg = check_remote_revocation_online(cleaned_key, current_hwid)
    if remote_msg:
        return False, remote_msg, {}

    # 1. Check Default Master Keys (100% Offline & Online, Universal)
    if cleaned_key in DEFAULT_MASTER_KEYS:
        master_info = DEFAULT_MASTER_KEYS[cleaned_key]
        return True, "✅ License Key ត្រឹមត្រូវ!", {
            "license_key": cleaned_key,
            "client_name": master_info.get("client_name", "Administrator"),
            "plan": master_info.get("plan", "LIFETIME"),
            "expires_at": "LIFETIME",
            "expiry_timestamp": 0,
            "bound_hwid": "ANY",
            "status": "ACTIVE"
        }

    # 2. Check Custom Keys defined by Admin
    custom_file = resolve_file_path("custom_keys.json")
    if custom_file.exists():
        try:
            with open(custom_file, "r", encoding="utf-8") as f:
                custom_dict = json.load(f)
            if cleaned_key in custom_dict:
                rec = custom_dict[cleaned_key]
                if rec.get("status") == "REVOKED":
                    return False, "❌ Custom Key នេះត្រូវបានផ្អាកដោយ Admin", {}

                bound_hwid = str(rec.get("bound_hwid", "ANY")).strip().upper()
                if bound_hwid not in ("ANY", "*", "", "NONE") and bound_hwid != current_hwid:
                    return False, "❌ Custom Key នេះត្រូវបានចាក់សោសម្រាប់តែម៉ាស៊ីនមួយប៉ុណ្ណោះ (HWID មិនត្រឹមត្រូវ)", {}

                expiry_ts = rec.get("expiry_timestamp", 0)
                if expiry_ts > 0 and time.time() > expiry_ts:
                    return False, f"⚠️ Custom Key នេះបានផុតកំណត់កាលបរិច្ឆេទហើយ ({rec.get('expires_at')})", {}

                return True, "✅ Custom Key ផ្ទាល់ខ្លួនត្រឹមត្រូវ និងសកម្ម!", rec
        except Exception:
            pass

    # 3. Check Admin History (if present on local Admin PC)
    history_file = resolve_file_path("admin_key_history.json")
    if history_file.exists():
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
                for record in history:
                    if record.get("license_key", "").strip().upper() == cleaned_key:
                        if record.get("status") == "REVOKED":
                            return False, "❌ License Key នេះត្រូវបានផ្អាកដោយ Admin", {}

                        bound_hwid = str(record.get("bound_hwid", "ANY")).strip().upper()
                        if bound_hwid not in ("ANY", "*", "", "NONE") and bound_hwid != current_hwid:
                            return False, "❌ License Key នេះត្រូវបានចាក់សោសម្រាប់តែម៉ាស៊ីនមួយប៉ុណ្ណោះ (HWID មិនត្រឹមត្រូវ)", {}

                        expiry_ts = record.get("expiry_timestamp", 0)
                        if expiry_ts > 0 and time.time() > expiry_ts:
                            return False, f"⚠️ License Key នេះបានផុតកំណត់កាលបរិច្ឆេទហើយ ({record.get('expires_at')})", {}

                        return True, "✅ License Key ត្រឹមត្រូវ និងសកម្ម!", record
        except Exception:
            pass

    # 4. Check Online Cloud Registry (GitHub) & Bundled Online Keys Database
    online_ok, online_msg, online_rec = check_key_online(cleaned_key, current_hwid)
    if online_ok:
        return True, online_msg, online_rec
    elif online_msg and ("ផ្អាក" in online_msg or "ផុតកំណត់" in online_msg or "HWID" in online_msg):
        return False, online_msg, {}

    # 5. Cryptographic Signature Offline Verification (Standard 6-part SN key)
    parts = cleaned_key.split("-")
    if len(parts) == 6 and parts[0] == "SN":
        _, plan_tag, expiry_code, hwid_tag, salt, sig = parts
        payload = f"SN:{plan_tag}:{expiry_code}:{hwid_tag}:{salt}"

        is_sig_valid = False
        for secret in [
            SECRET_ADMIN_SALT,
            "SN_TOOL_U_NICH_AI_DRAMA_STUDIO_2026",
            "SN_TOOL_VIP_KEY_2026_SECRET",
            "SN_STUDIO_MASTER_KEY_2026"
        ]:
            exp_sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest().upper()
            if sig == exp_sig[:len(sig)]:
                is_sig_valid = True
                break

        if not is_sig_valid:
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
            "client_name": "User",
            "plan": f"PRO_{plan_tag}",
            "expires_at": expiry_str,
            "expiry_timestamp": expiry_ts,
            "bound_hwid": current_hwid if hwid_tag not in ("9999", "AAAA") else "ANY",
            "status": "ACTIVE"
        }

    return False, "❌ License Key មិនត្រឹមត្រូវ សូមទាក់ទង Admin ដើម្បីទទួលយក Key", {}


def activate_license_on_device(license_key: str, client_name: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
    """Activate license key on the current computer, record customer name, and write to license.key."""
    current_hwid = get_machine_hwid()
    valid, msg, record = verify_license_key(license_key, current_hwid)
    if not valid:
        return False, msg, {}

    # Prefer user inputted client_name, fallback to record's client_name
    final_client_name = (client_name.strip() if client_name and client_name.strip() else None) or record.get("client_name", "User")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Write activation data to license.key
    data_to_save = {
        "license_key": license_key.strip().upper(),
        "client_name": final_client_name,
        "plan": record.get("plan", "PRO"),
        "activated_at": now_str,
        "last_active": now_str,
        "use_count": 1,
        "expires_at": record.get("expires_at", "LIFETIME"),
        "expiry_timestamp": record.get("expiry_timestamp", 0),
        "machine_hwid": current_hwid,
        "checksum": hmac.new(SECRET_ADMIN_SALT.encode(), f"{license_key.strip().upper()}|{current_hwid}".encode(), hashlib.sha256).hexdigest()[:16]
    }

    try:
        with open(LICENSE_FILE, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=2, ensure_ascii=False)
    except Exception as e:
        return False, f"Could not write license file: {e}", {}

    # Also update client_name and last_active in admin_key_history.json if present
    cleaned_key = license_key.strip().upper()
    if ADMIN_HISTORY_FILE.exists():
        try:
            with open(ADMIN_HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
            found = False
            for r in history:
                if r.get("license_key", "").strip().upper() == cleaned_key:
                    r["client_name"] = final_client_name
                    r["activated_at"] = now_str
                    r["last_active"] = now_str
                    r["use_count"] = int(r.get("use_count", 0)) + 1
                    r["active_hwid"] = current_hwid
                    found = True
                    break
            if not found:
                new_rec = {
                    "license_key": cleaned_key,
                    "client_name": final_client_name,
                    "plan": record.get("plan", "PRO"),
                    "duration_days": record.get("duration_days", 0),
                    "created_at": now_str,
                    "activated_at": now_str,
                    "last_active": now_str,
                    "use_count": 1,
                    "expires_at": record.get("expires_at", "LIFETIME"),
                    "expiry_timestamp": record.get("expiry_timestamp", 0),
                    "bound_hwid": current_hwid,
                    "status": "ACTIVE"
                }
                history.insert(0, new_rec)

            with open(ADMIN_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)

            sync_online_keys()
        except Exception:
            pass

    return True, f"🎉 បាន Activate License Key ជោគជ័យ! ស្វាគមន៍ {final_client_name}!", data_to_save


def check_current_device_license() -> Dict[str, Any]:
    """Check if the current device is activated with a valid license."""
    current_hwid = get_machine_hwid()

    # 0. Check if license requirement is disabled (Free / Open Access mode)
    if not is_license_required():
        return {
            "is_activated": True,
            "license_key": "FREE-OPEN-ACCESS",
            "client_name": "Free / Open User",
            "plan": "LIFETIME_UNLOCKED",
            "expires_at": "LIFETIME",
            "hwid": current_hwid,
            "message": "License Gate ត្រូវបានបិទ (បើកដំណើរការដោយសេរី Free 100%)"
        }

    # Strict License Protection: Require valid key entry if license.key does not exist
    lic_path = resolve_file_path("license.key")
    if not lic_path.exists():
        return {
            "is_activated": False,
            "message": "សូមបញ្ចូល License Key ដើម្បីបើកដំណើរការ Tool",
            "hwid": current_hwid
        }

    try:
        with open(lic_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        license_key = data.get("license_key", "").strip().upper()
        saved_hwid = data.get("machine_hwid", "").strip().upper()
        checksum = data.get("checksum", "")

        # Verify integrity
        expected_checksum = hmac.new(SECRET_ADMIN_SALT.encode(), f"{license_key}|{saved_hwid}".encode(), hashlib.sha256).hexdigest()[:16]
        if checksum != expected_checksum:
            return {
                "is_activated": False,
                "message": "License Key File ត្រូវបានកែបន្លំ",
                "hwid": current_hwid
            }

        # Check machine HWID match
        if saved_hwid != current_hwid:
            return {
                "is_activated": False,
                "message": "សូមបញ្ចូល License Key ដើម្បីបើកដំណើរការ Tool (Machine Mismatch)",
                "hwid": current_hwid
            }

        # Check local and remote revocation
        if license_key in get_revoked_keys():
            return {
                "is_activated": False,
                "message": "❌ License Key នេះត្រូវបាន Admin ផ្អាកការប្រើប្រាស់",
                "hwid": current_hwid
            }

        remote_msg = check_remote_revocation_online(license_key, current_hwid)
        if remote_msg:
            return {
                "is_activated": False,
                "message": remote_msg,
                "hwid": current_hwid
            }

        # Touch activity & calculate live dynamic status
        touch_license_activity(license_key, current_hwid)
        live = calculate_key_live_status(data)

        if live.get("is_expired"):
            return {
                "is_activated": False,
                "message": f"⚠️ License Key របស់អ្នកបានផុតកំណត់កាលពី {abs(live.get('days_remaining', 0))} ថ្ងៃមុន សូមទាក់ទង Admin ដើម្បីបន្តសុពលភាព",
                "hwid": current_hwid,
                "is_expired": True
            }

        return {
            "is_activated": True,
            "license_key": license_key,
            "client_name": data.get("client_name", "User"),
            "plan": data.get("plan", "PRO"),
            "expires_at": data.get("expires_at", "LIFETIME"),
            "days_remaining": live.get("days_remaining", 99999),
            "is_expiring_soon": live.get("is_expiring_soon", False),
            "status_kh": live.get("status_kh", "សកម្ម"),
            "last_active": data.get("last_active", "Just now"),
            "hwid": current_hwid,
            "message": "License សកម្ម ១០០%"
        }
    except Exception as e:
        return {
            "is_activated": False,
            "message": f"Error verifying license: {e}",
            "hwid": current_hwid
        }
