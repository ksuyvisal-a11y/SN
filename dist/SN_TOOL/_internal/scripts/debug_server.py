import sys
import os
import subprocess
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

res = subprocess.run(
    [str(PY_EXE), "server.py"],
    cwd=str(APP_DIR),
    env=env,
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
    timeout=10
)

print("Return code:", res.returncode)
print("STDOUT:\n", res.stdout)
print("STDERR:\n", res.stderr)
