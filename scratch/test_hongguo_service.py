import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import time
import socket
import subprocess
import urllib.request
import urllib.parse
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

HG_ROOT = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader")
JAVA_BIN = str(HG_ROOT / "jre" / "bin" / "java.exe")
SIGN_DIR = str(HG_ROOT / "app" / "sign")
JAR_PATH = "unidbg-sign.jar"
PYTHON_BIN = str(HG_ROOT / "python" / "python.exe")
APP_DIR = str(HG_ROOT / "app")
SERVER_PY = str(HG_ROOT / "app" / "server.py")

SIGN_PORT = 9099
API_PORT = 8000
API_BASE = f"http://127.0.0.1:{API_PORT}"

def is_port_open(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0

def wait_for_port(port: int, timeout_sec: int = 30) -> bool:
    start = time.time()
    while time.time() - start < timeout_sec:
        if is_port_open(port):
            return True
        time.sleep(0.5)
    return False

def ensure_hongguo_engine_running(save_dir: str = "D:/SN_Dramas") -> bool:
    """Ensure the local Hongguo signer and API server are up and ready."""
    if not Path(JAVA_BIN).exists() or not Path(PYTHON_BIN).exists():
        print("[HongguoService] Missing bundled components.")
        return False

    # 1. Start Java Signer if needed
    if not is_port_open(SIGN_PORT):
        print(f"[HongguoService] Starting unidbg signer on port {SIGN_PORT}...")
        cmd_java = [
            JAVA_BIN,
            "-Xmx1024m",
            "-XX:+ExitOnOutOfMemoryError",
            "--add-opens", "java.base/java.lang=ALL-UNNAMED",
            "-cp", JAR_PATH,
            "com.hongguo.sign.FqTrace",
            "serve",
            str(SIGN_PORT)
        ]
        # DETACHED_PROCESS on Windows
        DETACHED_PROCESS = 0x00000008
        CREATE_NO_WINDOW = 0x08000000
        subprocess.Popen(
            cmd_java,
            cwd=SIGN_DIR,
            creationflags=DETACHED_PROCESS | CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if not wait_for_port(SIGN_PORT, timeout_sec=35):
            print("[HongguoService] Signer failed to start in time.")
            return False
        print("[HongguoService] ✔ Signer is running.")

    # 2. Start Python Server if needed
    if not is_port_open(API_PORT):
        print(f"[HongguoService] Starting API server on port {API_PORT}...")
        env = os.environ.copy()
        env["SIGN_SERVER"] = f"http://127.0.0.1:{SIGN_PORT}"
        env["BIND_HOST"] = "127.0.0.1"
        env["PORT"] = str(API_PORT)
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["HG_OUT"] = str(save_dir)

        DETACHED_PROCESS = 0x00000008
        CREATE_NO_WINDOW = 0x08000000
        subprocess.Popen(
            [PYTHON_BIN, SERVER_PY],
            cwd=APP_DIR,
            env=env,
            creationflags=DETACHED_PROCESS | CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if not wait_for_port(API_PORT, timeout_sec=25):
            print("[HongguoService] Server failed to start in time.")
            return False
        print("[HongguoService] ✔ API server is running.")

    # 3. Configure output dir
    try:
        req = urllib.request.Request(
            f"{API_BASE}/dl/config",
            data=json.dumps({"output_dir": str(save_dir)}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=3) as res:
            pass
    except Exception:
        pass

    return True

if __name__ == "__main__":
    ok = ensure_hongguo_engine_running()
    print("Engine Running:", ok)
    if ok:
        try:
            with urllib.request.urlopen(f"{API_BASE}/dl/config", timeout=3) as res:
                print("Config:", json.loads(res.read().decode("utf-8")))
            with urllib.request.urlopen(f"{API_BASE}/dl/episodes?series_id=7683196130645003288", timeout=5) as res:
                eps = json.loads(res.read().decode("utf-8"))
                print(f"Verified series '{eps.get('title')}': {eps.get('total')} episodes available!")
        except Exception as e:
            print("Error:", e)
