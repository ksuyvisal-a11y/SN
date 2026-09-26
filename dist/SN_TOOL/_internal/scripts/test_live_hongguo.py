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

def is_port_open(port):
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0

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
    for _ in range(15):
        time.sleep(0.5)
        if is_port_open(9099):
            print("Java Signer ready!")
            break

app_path = r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app"
sys.path.insert(0, app_path)
os.environ["SIGN_SERVER"] = "http://127.0.0.1:9099"

import hongguo

print("Searching '东北话事人'...")
res = hongguo.search("东北话事人")
print("Search result type:", type(res))
if isinstance(res, list) and res:
    print(f"Found {len(res)} results:")
    for item in res[:3]:
        print(" - Series:", item.get("title"), "ID:", item.get("series_id"), "Episodes:", item.get("episode_cnt"))
        sid = item.get("series_id")
        if sid:
            print(f"Fetching episodes for series #{sid}...")
            eps = hongguo.get_episodes(sid)
            print(f"Total episodes returned: {len(eps)}")
            if eps:
                print("First episode keys:", list(eps[0].keys()))
                print("Episode 1 title:", eps[0].get("title"), "item_id:", eps[0].get("item_id"), "video_id:", eps[0].get("video_id"))
elif isinstance(res, dict):
    print("Search result dict keys:", list(res.keys()))
