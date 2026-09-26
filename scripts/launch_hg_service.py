import sys
import os
import time
import socket
import subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

HG_DIR = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader")
JAVA_EXE = HG_DIR / "jre" / "bin" / "java.exe"
SIGN_DIR = HG_DIR / "app" / "sign"
PY_EXE = HG_DIR / "python" / "python.exe"
APP_DIR = HG_DIR / "app"

def is_port_open(port):
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0

# 1. Check & start Java Signer on 9099
if not is_port_open(9099):
    print("Starting Java Signer on port 9099...")
    subprocess.Popen(
        [
            str(JAVA_EXE),
            "-Xmx1024m",
            "-XX:+ExitOnOutOfMemoryError",
            "--add-opens",
            "java.base/java.lang=ALL-UNNAMED",
            "-cp",
            "unidbg-sign.jar",
            "com.hongguo.sign.FqTrace",
            "serve",
            "9099"
        ],
        cwd=str(SIGN_DIR),
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS if os.name == 'nt' else 0
    )
    for _ in range(15):
        time.sleep(1)
        if is_port_open(9099):
            print("Java Signer is online!")
            break
    else:
        print("Java Signer startup timed out!")
else:
    print("Java Signer already online on 9099.")

# 2. Check & start Hongguo API Server on 8000
if not is_port_open(8000):
    print("Starting Hongguo Server on port 8000...")
    env = dict(os.environ)
    env["SIGN_SERVER"] = "http://127.0.0.1:9099"
    env["PORT"] = "8000"
    env["BIND_HOST"] = "127.0.0.1"
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    
    # We can launch via uvicorn directly: python -m uvicorn server:app --host 127.0.0.1 --port 8000
    subprocess.Popen(
        [
            str(PY_EXE),
            "-m",
            "uvicorn",
            "server:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000"
        ],
        cwd=str(APP_DIR),
        env=env,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS if os.name == 'nt' else 0
    )
    for _ in range(15):
        time.sleep(1)
        if is_port_open(8000):
            print("Hongguo Server is online!")
            break
    else:
        print("Hongguo Server startup timed out!")
else:
    print("Hongguo Server already online on 8000.")

print(f"Status: Signer(9099)={is_port_open(9099)}, API(8000)={is_port_open(8000)}")
