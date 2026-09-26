import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import time
import socket
import subprocess
import urllib.request
import json
from pathlib import Path

HG_ROOT = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader")
JAVA_BIN = str(HG_ROOT / "jre" / "bin" / "java.exe")
JAR_PATH = str(HG_ROOT / "app" / "sign" / "unidbg-sign.jar")
PYTHON_BIN = str(HG_ROOT / "python" / "python.exe")
SERVER_PY = str(HG_ROOT / "app" / "server.pyc")
APP_DIR = str(HG_ROOT / "app")

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(('127.0.0.1', port)) == 0

print("1. Starting Unidbg Signer...")
if not is_port_open(9099):
    cmd_java = [
        JAVA_BIN,
        "-Xmx1024m",
        "-XX:+ExitOnOutOfMemoryError",
        "--add-opens", "java.base/java.lang=ALL-UNNAMED",
        "-cp", JAR_PATH,
        "com.hongguo.sign.FqTrace",
        "serve",
        "9099"
    ]
    signer_proc = subprocess.Popen(cmd_java, cwd=str(HG_ROOT / "app" / "sign"), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for _ in range(30):
        if is_port_open(9099):
            print("✔ Signer is UP on port 9099!")
            break
        time.sleep(0.5)
else:
    print("Signer already open on 9099.")

print("2. Starting Server...")
if not is_port_open(8000):
    env = os.environ.copy()
    env["SIGN_SERVER"] = "http://127.0.0.1:9099"
    env["PORT"] = "8000"
    env["BIND_HOST"] = "127.0.0.1"
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["HG_OUT"] = "D:/SN_Dramas"
    cmd_srv = [PYTHON_BIN, SERVER_PY]
    srv_proc = subprocess.Popen(cmd_srv, cwd=APP_DIR, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for _ in range(30):
        if is_port_open(8000):
            print("✔ Server is UP on port 8000!")
            break
        time.sleep(0.5)
else:
    print("Server already open on 8000.")

print("3. Testing Server APIs...")
# Test /dl/resolve with 东北话事人 (7683196130645003288)
try:
    url = "http://127.0.0.1:8000/dl/resolve?url=7683196130645003288"
    with urllib.request.urlopen(url, timeout=10) as res:
        data = json.loads(res.read().decode('utf-8'))
        print("Resolve result:")
        print("  Title:", data.get("title"))
        print("  Series ID:", data.get("series_id"))
        print("  Episode count:", data.get("episode_cnt") or len(data.get("episodes", [])))
        if "episodes" in data:
            eps = data["episodes"]
            print("  Episodes len:", len(eps))
            if eps:
                print("  EP 1:", eps[0].get("title"), eps[0].get("video_id"))
                print("  EP 5:", eps[min(4, len(eps)-1)].get("title"), eps[min(4, len(eps)-1)].get("video_id"))
                print("  Last EP:", eps[-1].get("title"), eps[-1].get("video_id"))
except Exception as e:
    print("Resolve error:", e)

# Test /dl/episodes?series_id=7683196130645003288
try:
    url2 = "http://127.0.0.1:8000/dl/episodes?series_id=7683196130645003288"
    with urllib.request.urlopen(url2, timeout=10) as res2:
        data2 = json.loads(res2.read().decode('utf-8'))
        print("\n/dl/episodes result:")
        print("  Keys:", list(data2.keys()) if isinstance(data2, dict) else f"list({len(data2)})")
        if isinstance(data2, dict):
            eps2 = data2.get("episodes", [])
            print("  Episodes count:", len(eps2))
            if eps2:
                print("  EP 1:", eps2[0])
                print("  EP 50:", eps2[min(49, len(eps2)-1)])
except Exception as e:
    print("/dl/episodes error:", e)
