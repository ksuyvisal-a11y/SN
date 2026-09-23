import subprocess
import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path

dest = Path("D:/SN_Dramas/东北话事人/test_cn.mp4")
dest.parent.mkdir(parents=True, exist_ok=True)

cmd = [
    "curl.exe",
    "-k", "-L",
    "https://hongguoduanju.com/favicon.ico",
    "-o", str(dest)
]
print("Running curl with path:", str(dest))
r = subprocess.run(cmd, capture_output=True)
print("Returncode:", r.returncode)
print("Stdout:", r.stdout.decode('utf-8', errors='ignore'))
print("Stderr:", r.stderr.decode('utf-8', errors='ignore'))
print("Dest exists?", dest.exists())
