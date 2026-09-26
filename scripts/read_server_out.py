import sys
import os
import subprocess
import time
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
    [str(PY_EXE), "server.py"],
    cwd=str(APP_DIR),
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding="utf-8",
    errors="replace"
)

# Read output for up to 10 seconds
t0 = time.time()
while time.time() - t0 < 8:
    line = p.stdout.readline()
    if line:
        print("OUT:", line.strip())
    elif p.poll() is not None:
        print("Process exited with code:", p.poll())
        break
    time.sleep(0.1)

print("Process status poll:", p.poll())
p.terminate()
