import os
import sys
import time
import socket
import subprocess
from pathlib import Path

HG_ROOT = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader")
PYTHON_BIN = str(HG_ROOT / "python" / "python.exe")
APP_DIR = str(HG_ROOT / "app")
SERVER_PY = str(HG_ROOT / "app" / "server.py")

env = os.environ.copy()
env["SIGN_SERVER"] = "http://127.0.0.1:9099"
env["BIND_HOST"] = "127.0.0.1"
env["PORT"] = "8000"
env["PYTHONUTF8"] = "1"
env["PYTHONIOENCODING"] = "utf-8"
env["HG_OUT"] = "D:/SN_Dramas"

def is_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        return s.connect_ex(('127.0.0.1', port)) == 0

print("Launching server.py...")
proc = subprocess.Popen([PYTHON_BIN, SERVER_PY], cwd=APP_DIR, env=env)

opened = False
for sec in range(20):
    time.sleep(1)
    if is_open(8000):
        print(f"Port 8000 opened in {sec+1} seconds!")
        opened = True
        break
    else:
        print(f"Sec {sec+1}: port 8000 not open yet...")

if not opened:
    print("Port 8000 never opened in 20 seconds.")

proc.terminate()
