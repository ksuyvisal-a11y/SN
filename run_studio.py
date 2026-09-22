import sys
import os
import subprocess
import webbrowser
import threading
import time

# Enable utf-8 output in Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def free_port_8000():
    """Kill any stale process occupying port 8000 before starting new server."""
    if sys.platform == "win32":
        try:
            out = subprocess.check_output('netstat -ano | findstr :8000', shell=True).decode()
            current_pid = os.getpid()
            for line in out.strip().split('\n'):
                parts = line.strip().split()
                if len(parts) >= 5 and 'LISTENING' in line:
                    pid = int(parts[-1])
                    if pid != current_pid and pid > 0:
                        subprocess.run(f'taskkill /F /PID {pid}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

from server import app

def launch_native_window(url="http://127.0.0.1:8000", title="SN TOOL - STUDIO PRO"):
    """
    Launch SN TOOL as a dedicated native desktop software window:
    1. Try pywebview (Native Edge WebView2 window)
    2. Try Standalone App Window Mode via Microsoft Edge or Chrome (--app=)
    3. Fallback to default browser
    """
    time.sleep(1.0)
    # 1. Try pywebview
    try:
        import webview
        window = webview.create_window(
            title=title,
            url=url,
            width=1360,
            height=860,
            min_size=(1024, 680),
            background_color="#08090d"
        )
        webview.start()
        return
    except Exception as e:
        print(f"pywebview notice: {e}")

    # 2. Try Native Desktop App Mode via Edge or Chrome (Standalone window, zero browser chrome/tabs)
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
                cmd = [exe, f"--app={url}", "--window-size=1360,860"]
                proc = subprocess.Popen(cmd)
                proc.wait()
                return
            except Exception as e:
                print(f"App window mode notice: {e}")

    # 3. Fallback to default browser
    import webbrowser
    webbrowser.open(url)

if __name__ == "__main__":
    free_port_8000()
    os.makedirs("cache/audio_cache", exist_ok=True)
    os.makedirs("data/projects", exist_ok=True)
    os.makedirs("data/uploads", exist_ok=True)

    print("\n========================================================")
    print(" 🎬 កំពុងដំណើរការ SN TOOL - STUDIO PRO (Native Desktop App)...")
    print(" 🎙️ សំឡេងខ្មែរផ្លូវការ: ពិសិដ្ឋ (Piseth) & ស្រីមុំ (Sreymom)")
    print("========================================================\n")

    # Run server in daemon thread
    server_thread = threading.Thread(target=lambda: app.run(host="127.0.0.1", port=8000, debug=False, use_reloader=False), daemon=True)
    server_thread.start()

    # Launch native desktop application window
    launch_native_window()
