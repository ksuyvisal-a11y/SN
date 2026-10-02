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

def is_window_zoomed():
    """Check if the native window is currently maximized."""
    global _main_window
    if not _main_window:
        return False

    # 1. Native WinForms WindowState check
    try:
        if hasattr(_main_window, 'native') and _main_window.native:
            ws = getattr(_main_window.native, 'WindowState', None)
            if ws is not None:
                ws_str = str(ws)
                if 'Maximized' in ws_str or ws_str == '2':
                    return True
    except Exception:
        pass

    # 2. Windows Win32 API IsZoomed check with proper IntPtr Handle extraction
    try:
        if sys.platform == "win32":
            import ctypes
            hwnd = None
            if hasattr(_main_window, 'native') and _main_window.native:
                try:
                    h = _main_window.native.Handle
                    hwnd = int(str(h)) if hasattr(h, 'ToString') else int(h.ToInt64())
                except Exception:
                    try:
                        hwnd = int(h.ToInt32())
                    except Exception:
                        pass
            if not hwnd:
                hwnd = ctypes.windll.user32.FindWindowW(None, "SN TOOL - STUDIO PRO")
            if hwnd:
                return bool(ctypes.windll.user32.IsZoomed(hwnd))
    except Exception:
        pass

    # 3. Geometry check against primary monitor screen bounds
    try:
        import webview
        screens = getattr(webview, 'screens', None)
        s = screens[0] if screens else None
        if s and hasattr(_main_window, 'width') and hasattr(_main_window, 'height'):
            if _main_window.width >= (s.width - 35) and _main_window.height >= (s.height - 75):
                return True
    except Exception:
        pass

    return False

class NativeWindowApi:
    def __init__(self):
        self._is_maximized = False

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
                was_zoomed = is_window_zoomed() or self._is_maximized
                if was_zoomed:
                    _main_window.restore()
                    self._is_maximized = False
                    return {"maximized": False}
                else:
                    _main_window.maximize()
                    self._is_maximized = True
                    return {"maximized": True}
            except Exception:
                try:
                    _main_window.maximize()
                    self._is_maximized = True
                    return {"maximized": True}
                except Exception:
                    pass
        return {"maximized": False}

    def is_window_maximized(self):
        return is_window_zoomed() or self._is_maximized

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
                self._is_maximized = True
            except Exception:
                pass

    def close_window(self):
        global _main_window
        if _main_window:
            try:
                _main_window.destroy()
            except Exception:
                pass

def get_standard_window_geometry():
    """
    Calculate ideal desktop window size & centered coordinates.
    Provides standard desktop app dimensions (similar to CapCut, Photoshop, Telegram, Filmora):
    - Width: ~72-74% of screen width (e.g. 1380px on 1080p)
    - Height: ~78-82% of screen height (e.g. 840px on 1080p)
    - Centered on primary monitor
    - Taskbar completely visible and unobstructed
    """
    sw, sh = 1920, 1080
    try:
        import webview
        screens = getattr(webview, 'screens', None)
        if screens and len(screens) > 0:
            sw = screens[0].width
            sh = screens[0].height
    except Exception:
        pass

    # Bounded ideal dimensions
    if sw >= 2560:  # 2K / 4K
        win_w = 1600
        win_h = 980
    elif sw >= 1920:  # 1080p (Standard Full HD)
        win_w = 1380
        win_h = 840
    elif sw >= 1600:  # 900p / 1600x900
        win_w = 1280
        win_h = 780
    else:  # 1366x768 or smaller laptop
        win_w = min(1200, sw - 50)
        win_h = min(700, sh - 60)

    # Position in center of screen
    x = max(0, (sw - win_w) // 2)
    y = max(10, (sh - win_h - 48) // 2)  # accounting for ~48px Windows taskbar

    return win_w, win_h, x, y

def launch_native_window(url="http://127.0.0.1:8000", title="SN TOOL - STUDIO PRO"):
    """
    Open application in a dedicated standalone native desktop window:
    1. Try pywebview (Edge WebView2 native embed) in standard centered desktop window size
    2. Try Standalone App Window Mode via Microsoft Edge or Google Chrome (--app=) centered
    3. Fallback to default browser
    """
    win_w, win_h, x, y = get_standard_window_geometry()

    # 1. Try pywebview
    try:
        import webview
        global _main_window

        api = NativeWindowApi()
        window = webview.create_window(
            title=title,
            url=url,
            frameless=True,
            easy_drag=False,  # Prevent pywebview's buggy global mousedown listener from moving window on right-click or arbitrary clicks
            shadow=True,
            maximized=False,
            width=win_w,
            height=win_h,
            x=x,
            y=y,
            resizable=True,
            min_size=(1024, 650),
            background_color="#08090d",
            text_select=True,
            zoomable=True,
            js_api=api
        )
        _main_window = window

        # Safeguard move calls: NEVER move or drag window when it is maximized
        try:
            orig_move = window.move
            def safe_window_move(x, y):
                try:
                    if is_window_zoomed() or api._is_maximized:
                        return  # Window is MAXIMIZED: strictly block any dragging/movement!
                except Exception:
                    pass
                return orig_move(x, y)
            window.move = safe_window_move
        except Exception:
            pass

        # Native event listeners to synchronize maximized state to frontend immediately
        def on_window_maximized():
            try:
                api._is_maximized = True
                window.evaluate_js("setWindowMaximizedState(true)")
            except Exception:
                pass

        def on_window_restored():
            try:
                api._is_maximized = False
                window.evaluate_js("setWindowMaximizedState(false)")
            except Exception:
                pass

        try:
            window.events.maximized += on_window_maximized
            window.events.restored += on_window_restored
        except Exception:
            pass

        def on_gui_ready(w):
            if sys.platform == "win32":
                try:
                    import ctypes
                    hwnd = None
                    if hasattr(w, 'native') and w.native:
                        try:
                            hwnd = int(w.native.Handle)
                        except Exception:
                            pass
                    if not hwnd:
                        hwnd = ctypes.windll.user32.FindWindowW(None, title)
                    if hwnd:
                        DWMWA_WINDOW_CORNER_PREFERENCE = 33
                        DWMWCP_ROUND = 2
                        pref = ctypes.c_int(DWMWCP_ROUND)
                        ctypes.windll.dwmapi.DwmSetWindowAttribute(
                            hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, ctypes.byref(pref), ctypes.sizeof(pref)
                        )
                        DWMWA_BORDER_COLOR = 34
                        # Signature Gold (#facc15 -> R:0xFA, G:0xCC, B:0x15 -> BGR: 0x0015CCFA)
                        color = ctypes.c_int(0x0015CCFA)
                        ctypes.windll.dwmapi.DwmSetWindowAttribute(
                            hwnd, DWMWA_BORDER_COLOR, ctypes.byref(color), ctypes.sizeof(color)
                        )
                except Exception:
                    pass

        webview.start(on_gui_ready, window, private_mode=False, gui='edgechromium')
        return
    except Exception as e:
        print(f"pywebview notice: {e}")

    # 2. Try Native Desktop App Mode via Edge or Chrome (Standalone window, zero browser chrome/tabs, centered)
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
                cmd = [exe, f"--app={url}", f"--window-size={win_w},{win_h}", f"--window-position={x},{y}"]
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
