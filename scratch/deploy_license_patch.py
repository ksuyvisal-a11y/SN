from pathlib import Path

target_file = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app\licensing.py")

licensing_code = '''"""
Hongguo Downloader Unlimited Lifetime License Provider
Enables 100% unrestricted batch downloads for all 49,509+ Hongguo short dramas.
"""

def _load_creds():
    return {"url": "", "anon_key": ""}

def _machine_guid():
    return "mg:sn-tool-pro-unlimited"

def _state_dir():
    return ""

def _load_state():
    return {}

def _save_state(d):
    pass

def device_id():
    return "d1:sn-tool-pro-unlimited-device"

def device_label():
    return "SN TOOL STUDIO PRO (Lifetime Unlimited)"

def _mask(key):
    return "SN-PRO-****-LIFETIME"

def _rpc(fn, payload):
    return {"allowed": True, "licensed": True}

def enforced():
    return False

def ensure_checked():
    pass

def is_active_cached():
    return True

def _apply_result(res, key):
    pass

def _refresh():
    pass

def activate(key):
    return {
        "ok": True,
        "active": True,
        "licensed": True,
        "key_masked": "SN-PRO-****-LIFETIME",
        "device_label": "SN TOOL STUDIO PRO",
        "expires_at": "2099-12-31T23:59:59Z"
    }

def deactivate():
    return {"ok": True}

def status():
    return {
        "active": True,
        "licensed": True,
        "enforced": False,
        "key_masked": "SN-PRO-****-LIFETIME",
        "expires_at": "2099-12-31T23:59:59Z",
        "device_label": "SN TOOL STUDIO PRO (Lifetime VIP)"
    }

def check_download(series_id):
    """Authorise downloading unlimited series without any quota limits."""
    return {
        "allowed": True,
        "licensed": True,
        "reason": "lifetime_vip",
        "free_used": 0,
        "free_limit": 9999999
    }

def _fetch_usage():
    return {
        "licensed": True,
        "remaining": 9999999,
        "free_limit": 9999999,
        "free_used": 0,
        "expires_at": "2099-12-31T23:59:59Z"
    }

def usage():
    return {
        "licensed": True,
        "remaining": 9999999,
        "free_limit": 9999999,
        "free_used": 0,
        "expires_at": "2099-12-31T23:59:59Z"
    }

def current_key():
    return "SN-PRO-LIFETIME-VIP"

def init():
    pass
'''

target_file.write_text(licensing_code, encoding="utf-8")
print(f"Successfully wrote {target_file}!")
