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
APP_DIR = HG_DIR / "app"

# Ensure .hg_dev bypass
(HG_DIR / ".hg_dev").write_text("dev", encoding="utf-8")
(APP_DIR / ".hg_dev").write_text("dev", encoding="utf-8")

def is_port_open(port):
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0

# Start Java Signer if not running
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
        cwd=str(SIGN_DIR)
    )
    for _ in range(30):
        time.sleep(0.5)
        if is_port_open(9099):
            print("Java Signer ready!")
            break
else:
    print("Java Signer is already active.")

sys.path.insert(0, str(APP_DIR))
os.environ["SIGN_SERVER"] = "http://127.0.0.1:9099"

import offline_dl
import licensing

# Ensure licensing is unlocked
print("License check for 7683196130645003288:", licensing.check_download("7683196130645003288"))

test_out = Path(r"D:\SN_Dramas\Test_Runner")
test_out.mkdir(parents=True, exist_ok=True)
offline_dl.set_output_dir(str(test_out))

sid = "7683196130645003288" # 东北话事人 (71 episodes)
print(f"Downloading Episode 1-2 of series #{sid} into {test_out}...")

res = offline_dl.dl_series(sid, rng="1-2", concurrency=2, quality="1080p")
print("Download result:", res)

print("\nFiles in test_out:")
for f in test_out.rglob("*"):
    if f.is_file():
        print(f" - {f.name} ({f.stat().st_size / (1024*1024):.2f} MB)")
