import sys
import os
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
    os.makedirs("cache/audio_cache", exist_ok=True)
    os.makedirs("data/projects", exist_ok=True)
    os.makedirs("data/uploads", exist_ok=True)
    
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host="0.0.0.0", port=8000, debug=False)

