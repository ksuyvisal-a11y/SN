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

# Ensure .hg_dev exists
(HG_DIR / ".hg_dev").write_text("dev", encoding="utf-8")
(APP_DIR / ".hg_dev").write_text("dev", encoding="utf-8")

DETACHED_FLAGS = 0x00000008 | 0x00000200 # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP

# 1. Signer
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
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=DETACHED_FLAGS
    )
    for _ in range(15):
        time.sleep(0.5)
        if is_port_open(9099):
            print("Java Signer ready!")
            break
else:
    print("Java Signer already running on 9099.")

# 2. Server
if not is_port_open(8000):
    print("Starting Hongguo Server on port 8000...")
    env = dict(os.environ)
    env["SIGN_SERVER"] = "http://127.0.0.1:9099"
    env["PORT"] = "8000"
    env["BIND_HOST"] = "127.0.0.1"
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    
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
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=DETACHED_FLAGS
    )
    for _ in range(15):
        time.sleep(0.5)
        if is_port_open(8000):
            print("Hongguo Server ready!")
            break
else:
    print("Hongguo Server already running on 8000.")

print(f"Signer online: {is_port_open(9099)}, Server online: {is_port_open(8000)}")
