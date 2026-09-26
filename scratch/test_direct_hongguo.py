import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import time
import socket
import subprocess
from pathlib import Path

HG_ROOT = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader")
JAVA_BIN = HG_ROOT / "jre" / "bin" / "java.exe"
JAR_PATH = HG_ROOT / "app" / "sign" / "unidbg-sign.jar"
APP_DIR = HG_ROOT / "app"

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(('127.0.0.1', port)) == 0

if not is_port_open(9099):
    print("Starting unidbg signer...")
    cmd_java = [
        str(JAVA_BIN),
        "-Xmx1024m",
        "-XX:+ExitOnOutOfMemoryError",
        "--add-opens", "java.base/java.lang=ALL-UNNAMED",
        "-cp", str(JAR_PATH),
        "com.hongguo.sign.FqTrace",
        "serve",
        "9099"
    ]
    subprocess.Popen(cmd_java, cwd=str(HG_ROOT / "app" / "sign"))
    for _ in range(30):
        if is_port_open(9099):
            print("✔ Signer is up!")
            break
        time.sleep(0.5)

# Add app directory to sys.path
sys.path.insert(0, str(APP_DIR))
os.environ["SIGN_SERVER"] = "http://127.0.0.1:9099"

import hongguo

print("Testing hongguo.get_episodes for series 7683196130645003288 (东北话事人)...")
try:
    eps_data = hongguo.get_episodes("7683196130645003288")
    print("Type of eps_data:", type(eps_data))
    if isinstance(eps_data, dict):
        print("Keys:", list(eps_data.keys()))
        for k in eps_data:
            val = eps_data[k]
            if isinstance(val, list):
                print(f"  {k}: list of len {len(val)}")
            elif isinstance(val, dict):
                print(f"  {k}: dict with keys {list(val.keys())}")
            else:
                print(f"  {k}: {val}")
                
        # Now let's test get_video_urls or get_video_tracks!
        ep_list = eps_data.get("episodes") or eps_data.get("video_list") or []
        if ep_list:
            ep1 = ep_list[0]
            print("\nFirst episode structure:", ep1)
            # Try to get stream url for EP 1, EP 2, EP 4, EP 10!
            test_ep_vids = []
            for ep in ep_list[:5]:
                if isinstance(ep, dict):
                    v = ep.get("video_id") or ep.get("vid") or ep.get("item_id")
                    if v: test_ep_vids.append(v)
            print("Extracted test vids:", test_ep_vids)
            if test_ep_vids:
                tracks = hongguo.get_video_tracks(test_ep_vids)
                print(f"get_video_tracks result ({len(tracks)}):")
                for vid, trk in tracks.items():
                    print(f"  VID {vid}:")
                    if isinstance(trk, dict):
                        print("    track keys:", list(trk.keys()))
                        print("    main_url:", trk.get("main_url", "")[:80])
                        print("    video_url:", trk.get("video_url", "")[:80])
                    else:
                        print("    val:", str(trk)[:100])
except Exception as e:
    import traceback
    print("Error:", e)
    traceback.print_exc()
