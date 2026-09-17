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

def open_browser():
    time.sleep(1.2)
    url = "http://localhost:8000"
    print(f"\n========================================================")
    print(f" 🎬 Khmer AI Drama Studio កំពុងដំណើរការ!")
    print(f" 🌐 បើក Browser ទៅកាន់: {url}")
    print(f" 🎙️ សំឡេងខ្មែរផ្លូវការ: ពិសិដ្ឋ (Piseth) & ស្រីមុំ (Sreymom)")
    print(f"========================================================\n")
    webbrowser.open(url)

if __name__ == "__main__":
    free_port_8000()
    os.makedirs("cache/audio_cache", exist_ok=True)
    os.makedirs("data/projects", exist_ok=True)
    os.makedirs("data/uploads", exist_ok=True)
    
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host="0.0.0.0", port=8000, debug=False)
