"""
⚡ SN TOOL - Admin License Key Generator Dashboard Launcher
"""
import sys
import os
import time
import threading
import urllib.request
import webbrowser

# Enable utf-8 terminal output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def is_server_running():
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/api/license/status", timeout=1) as r:
            return r.status == 200
    except Exception:
        return False

def start_background_server():
    from server import app
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host="127.0.0.1", port=8000, debug=False, use_reloader=False)

def main():
    print("========================================================")
    print(" ⚡ SN TOOL - ADMIN LICENSE KEY GENERATOR DASHBOARD")
    print(" 🔐 ប្រព័ន្ធបង្កើត និងគ្រប់គ្រង KEY ជូនទៅកាន់ CUSTOMER")
    print("========================================================")

    if not is_server_running():
        print(" [1/2] Starting Local Server Engine...")
        server_thread = threading.Thread(target=start_background_server, daemon=True)
        server_thread.start()
        time.sleep(1.0)
    else:
        print(" [1/2] Connected to running Studio Server...")

    admin_url = "http://127.0.0.1:8000/admin"
    print(f" [2/2] Opening Dashboard GUI: {admin_url}\n")

    # Try launching native desktop window with pywebview
    try:
        import webview
        window = webview.create_window(
            title="SN TOOL - STUDIO PRO (Admin License Key Generator)",
            url=admin_url,
            width=680,
            height=820,
            resizable=True,
            background_color="#090a0e"
        )
        webview.start()
    except Exception as e:
        print(f"Opening in default web browser...")
        webbrowser.open(admin_url)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nExiting Admin Dashboard...")

if __name__ == "__main__":
    main()
