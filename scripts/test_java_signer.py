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

print("Port 9099 open:", is_port_open(9099))
print("Port 8000 open:", is_port_open(8000))

# Test starting Java if not running
if not is_port_open(9099):
    print("Starting Java signer on 9099...")
    java_cmd = [
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
    ]
    p_java = subprocess.Popen(
        java_cmd,
        cwd=str(SIGN_DIR),
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS if os.name == 'nt' else 0
    )
    print("Java spawned with PID:", p_java.pid)
    
    for i in range(30):
        time.sleep(1)
        if is_port_open(9099):
            print(f"Java signer ready after {i+1}s!")
            break
    else:
        print("Java signer timed out!")

print("Port 9099 now:", is_port_open(9099))
