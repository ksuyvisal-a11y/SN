"""
Khmer AI Drama Voice Translator & Movie Recap Studio - Native Desktop Application
Combines the backend server and embedded native desktop window.
"""
import sys
import os
import time
import threading
import multiprocessing
from pathlib import Path

# Required for PyInstaller frozen applications on Windows
multiprocessing.freeze_support()

# Protect against any accidental child process execution
if len(sys.argv) > 1 and sys.argv[1] in ("-c", "--help", "-h"):
    sys.exit(0)

# Enable native Per-Monitor V2 High DPI on Windows (crystal clear UI & dialogs)
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except Exception:
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                import ctypes
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass
# Safe stdout/stderr fallback for windowed / GUI mode where sys.stdout is None
class _SafeStream:
    def write(self, s): pass
    def flush(self): pass
    def reconfigure(self, **kwargs): pass
    def isatty(self): return False

if sys.stdout is None:
    sys.stdout = _SafeStream()
else:
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

if sys.stderr is None:
    sys.stderr = _SafeStream()
else:
    try:
        if hasattr(sys.stderr, 'reconfigure'):
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

import subprocess
from audio_processor import patch_silent_subprocess, get_silent_kwargs

patch_silent_subprocess()

def free_port_8000():
    """Clean stale listener on port 8000 before starting new server."""
    if sys.platform == "win32":
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                in_use = (s.connect_ex(('127.0.0.1', 8000)) == 0)
            if not in_use:
                return

            out = subprocess.check_output('netstat -ano | findstr :8000', shell=True, **get_silent_kwargs()).decode()
            current_pid = os.getpid()
            for line in out.strip().split('\n'):
                parts = line.strip().split()
                if len(parts) >= 5 and 'LISTENING' in line:
                    pid = int(parts[-1])
                    if pid != current_pid and pid > 0:
                        subprocess.run(f'taskkill /F /PID {pid}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **get_silent_kwargs())
        except Exception:
            pass

from server import app

def start_server():
    """Run Flask server in background thread."""
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host="127.0.0.1", port=8000, debug=False, use_reloader=False)

_main_window = None
class NativeWindowApi:
    def minimize_window(self):
        global _main_window
        if _main_window:
            try:
                _main_window.minimize()
            except Exception:
                pass

    def maximize_window(self):
        global _main_window
        if _main_window:
            try:
                import webview
                screens = getattr(webview, 'screens', None)
                s = screens[0] if screens else None
                sw = s.width if s else 1920
                sh = s.height if s else 1080
                # If window is already filling 90% of screen width and 85% of height, toggle restore
                if _main_window.width >= int(sw * 0.9) and _main_window.height >= int(sh * 0.85):
                    _main_window.restore()
                else:
                    _main_window.maximize()
            except Exception:
                try:
                    _main_window.maximize()
                except Exception:
                    pass

    def toggle_fullscreen(self):
        global _main_window
        if _main_window:
            try:
                _main_window.toggle_fullscreen()
            except Exception:
                pass

    def force_maximize(self):
        global _main_window
        if _main_window:
            try:
                _main_window.maximize()
            except Exception:
                pass

    def close_window(self):
        global _main_window
        if _main_window:
            try:
                _main_window.destroy()
            except Exception:
                pass

def launch_native_window(url="http://127.0.0.1:8000", title="SN TOOL - STUDIO PRO"):
    """
    Open application in a dedicated standalone native desktop window:
    1. Try pywebview (Edge WebView2 native embed) in maximized mode
    2. Try Standalone App Window Mode via Microsoft Edge or Google Chrome (--app=) maximized
    3. Fallback to default browser
    """
    # 1. Try pywebview
    try:
        import webview
        global _main_window
        screens = getattr(webview, 'screens', None)
        s = screens[0] if screens else None
        sw = s.width if s else 1536
        sh = s.height if s else 864

        api = NativeWindowApi()
        window = webview.create_window(
            title=title,
            url=url,
            frameless=True,
            easy_drag=True,
            maximized=True,
            width=sw,
            height=sh,
            x=0,
            y=0,
            min_size=(1024, 680),
            background_color="#08090d",
            text_select=True,
            zoomable=True,
            js_api=api
        )
        _main_window = window

        def on_gui_ready(w):
            try:
                time.sleep(0.2)
                w.maximize()
            except Exception:
                pass

        webview.start(on_gui_ready, window, private_mode=False, gui='edgechromium')
        return
    except Exception as e:
        print(f"pywebview notice: {e}")

    # 2. Try Native Desktop App Mode via Edge or Chrome (Standalone window, zero browser chrome/tabs, maximized)
    app_browsers = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for exe in app_browsers:
        if os.path.exists(exe):
            try:
                cmd = [exe, f"--app={url}", "--start-maximized", "--window-position=0,0"]
                t0 = time.time()
                proc = subprocess.Popen(cmd)
                proc.wait()
                if time.time() - t0 > 3.0:
                    return
            except Exception as e:
                print(f"App window mode notice: {e}")

    # 3. Fallback to default browser
    import webbrowser
    webbrowser.open(url)

def main():
    print("========================================================")
    print(" 🎬 កំពុងចាប់ផ្តើម SN TOOL - STUDIO PRO (Native Desktop App)...")
    print(" 🎙️ សំឡេងខ្មែរផ្លូវការ: ពិសិដ្ឋ (Piseth) & ស្រីមុំ (Sreymom)")
    print(" 🌐 Server Address: http://127.0.0.1:8000")
    print("========================================================")

    # 1. Clean port 8000
    free_port_8000()

    # 2. Start server in daemon thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(1.0)

    # 3. Launch native window
    launch_native_window()

    # 4. Clean exit once native window is closed
    sys.exit(0)

if __name__ == "__main__":
    main()
