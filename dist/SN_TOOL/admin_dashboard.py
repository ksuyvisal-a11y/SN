"""
👑 SN TOOL - VIP License Dashboard (Admin Control Center)
Launches the local Flask server and opens the Orion Light Admin Dashboard in the web browser.
"""
import sys
import os
import time
import threading
import urllib.request
import webbrowser
from pathlib import Path

# Ensure app directory is current directory
BASE_DIR = Path(__file__).resolve().parent
os.chdir(str(BASE_DIR))

# Safe stdout / stderr encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def is_server_running() -> bool:
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/api/license/status", timeout=1) as r:
            return r.status == 200
    except Exception:
        return False

def open_browser_when_ready(url: str, max_wait: float = 12.0):
    t_end = time.time() + max_wait
    while time.time() < t_end:
        if is_server_running():
            print(f"\n[OK] Server is ready! Opening browser: {url}")
            try:
                webbrowser.open(url)
            except Exception as e:
                print(f"[WARN] Could not auto-launch browser: {e}")
            return
        time.sleep(0.3)
    print(f"\n[WARN] Server startup wait finished. Opening browser: {url}")
    try:
        webbrowser.open(url)
    except Exception:
        pass

def main():
    admin_url = "http://127.0.0.1:8000/admin"
    print("=" * 65)
    print(" 👑 SN TOOL - VIP LICENSE ADMIN CONTROL DASHBOARD")
    print(" 🌐 URL: http://127.0.0.1:8000/admin")
    print("=" * 65)

    if is_server_running():
        print("[OK] Server is already running on port 8000.")
        print(f"[OK] Opening browser: {admin_url}")
        webbrowser.open(admin_url)
        print("\n✅ Admin Dashboard is open in your browser.")
        print("You can keep or close this console window.")
        return

    print("[1/2] Starting Studio Engine server on http://127.0.0.1:8000 ...")
    # Launch browser opener thread
    threading.Thread(target=open_browser_when_ready, args=(admin_url,), daemon=True).start()

    # Import and run Flask server
    import logging
    from server import app
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    print("[2/2] Server running. Press Ctrl+C in this console to stop.")
    try:
        app.run(host="127.0.0.1", port=8000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    main()
