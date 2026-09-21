"""
Khmer AI Drama Voice Translator & Movie Recap Studio - Native Desktop Application
Combines the backend server and embedded native desktop window.
"""
import sys
import os
import time
import threading
from pathlib import Path

# Enable utf-8 output in Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure working directory is set to app base directory
if getattr(sys, 'frozen', False):
    # Running as compiled executable (PyInstaller)
    BASE_DIR = Path(sys._MEIPASS)
    APP_DIR = Path(os.path.dirname(sys.executable))
else:
    # Running as script
    BASE_DIR = Path(__file__).resolve().parent
    APP_DIR = BASE_DIR

os.chdir(str(APP_DIR))
os.makedirs(str(APP_DIR / "cache" / "audio_cache"), exist_ok=True)
os.makedirs(str(APP_DIR / "data" / "projects"), exist_ok=True)
os.makedirs(str(APP_DIR / "data" / "uploads"), exist_ok=True)

from server import app

def start_server():
    """Run Flask server in background thread."""
    # Suppress verbose logging in desktop mode
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host="127.0.0.1", port=8000, debug=False, use_reloader=False)

def main():
    print("========================================================")
    print(" 🎬 កំពុងចាប់ផ្តើម Khmer AI Drama Voice Studio Desktop...")
    print(" 🎙️ សំឡេងខ្មែរផ្លូវការ: ពិសិដ្ឋ (Piseth) & ស្រីមុំ (Sreymom)")
    print("========================================================")

    # 1. Start server in daemon thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(1.0)

    # 2. Try launching Native Desktop Window via pywebview
    launched_native = False
    try:
        import webview
        launched_native = True
        window = webview.create_window(
            title="SN TOOL - STUDIO PRO",
            url="http://127.0.0.1:8000",
            width=1360,
            height=860,
            min_size=(1024, 680),
            background_color="#08090d"
        )
        webview.start()
    except Exception as e:
        print(f"Note: pywebview native window note ({e}), falling back to browser window.")
        import webbrowser
        webbrowser.open("http://127.0.0.1:8000")
        
        # Keep server running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nExiting...")

if __name__ == "__main__":
    main()
