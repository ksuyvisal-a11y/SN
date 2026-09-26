import sys
import os
import time
import socket
import subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

HG_DIR = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader")
PY_EXE = HG_DIR / "python" / "python.exe"
APP_DIR = HG_DIR / "app"

def is_port_open(port):
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0

print("Port 8000 open:", is_port_open(8000))

if not is_port_open(8000):
    print("Starting Hongguo server on 8000...")
    env = dict(os.environ)
    env["SIGN_SERVER"] = "http://127.0.0.1:9099"
    env["PORT"] = "8000"
    env["BIND_HOST"] = "127.0.0.1"
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    
    server_cmd = [
        str(PY_EXE),
        "server.py"
    ]
    p_srv = subprocess.Popen(
        server_cmd,
        cwd=str(APP_DIR),
        env=env,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS if os.name == 'nt' else 0
    )
    print("Hongguo server spawned with PID:", p_srv.pid)
    
    for i in range(15):
        time.sleep(1)
        if is_port_open(8000):
            print(f"Hongguo server ready after {i+1}s!")
            break
    else:
        print("Hongguo server timed out!")

print("Port 8000 now:", is_port_open(8000))
