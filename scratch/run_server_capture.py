import os
import sys
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

print("Running server.py directly...")
proc = subprocess.run([PYTHON_BIN, SERVER_PY], cwd=APP_DIR, env=env, capture_output=True, text=True, timeout=5)
print("Returncode:", proc.returncode)
print("STDOUT:", proc.stdout[:1000])
print("STDERR:", proc.stderr[:1000])
