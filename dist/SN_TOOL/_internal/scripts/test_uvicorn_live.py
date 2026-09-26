import sys
import os
import subprocess
import time
import socket
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

HG_DIR = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader")
PY_EXE = HG_DIR / "python" / "python.exe"
APP_DIR = HG_DIR / "app"

env = dict(os.environ)
env["SIGN_SERVER"] = "http://127.0.0.1:9099"
env["PORT"] = "8000"
env["BIND_HOST"] = "127.0.0.1"
env["PYTHONUTF8"] = "1"
env["PYTHONIOENCODING"] = "utf-8"

p = subprocess.Popen(
    [str(PY_EXE), "-m", "uvicorn", "server:app", "--host", "127.0.0.1", "--port", "8000"],
    cwd=str(APP_DIR),
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding="utf-8",
    errors="replace"
)

def is_port_open(port):
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0

for i in range(10):
    time.sleep(1)
    if is_port_open(8000):
        print(f"Port 8000 is open after {i+1}s!")
        break
    if p.poll() is not None:
        print("Process died! Exit code:", p.poll())
        break
else:
    print("Port 8000 not open yet.")

print("Port 8000 open:", is_port_open(8000))
# Read whatever stdout is available
out, _ = p.communicate(timeout=2)
print("Output from uvicorn:\n", out)
