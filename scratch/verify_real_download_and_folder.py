import sys
sys.stdout.reconfigure(encoding='utf-8')
import urllib.request
import json
import time

base = "http://127.0.0.1:8000"

print("1. Testing drama detail...")
req = urllib.request.Request(f"{base}/api/downloader/drama/hg_7683196130645003288")
with urllib.request.urlopen(req, timeout=5) as r:
    data = json.loads(r.read())
    print("Drama title:", data["drama"]["title"])
    print("Episodes count:", len(data["episodes"]))

print("\n2. Testing single episode real download...")
dl_req = urllib.request.Request(
    f"{base}/api/downloader/download-episodes",
    data=json.dumps({
        "episode_ids": ["ep_1"],
        "save_location": "D:/SN_Dramas",
        "save_poster": True
    }).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(dl_req, timeout=5) as r:
    print("Download start resp:", r.read().decode())

# Poll status for 15 seconds
for i in range(15):
    time.sleep(1)
    st_req = urllib.request.Request(f"{base}/api/downloader/status")
    with urllib.request.urlopen(st_req, timeout=5) as r:
        st_data = json.loads(r.read())
        is_dl = st_data.get("is_downloading")
        stats = st_data.get("stats")
        last_dir = st_data.get("last_download_dir")
        print(f"[{i+1}s] is_downloading={is_dl}, stats={stats}, last_dir={last_dir}")
        if not is_dl:
            print("Finished download!")
            for line in st_data.get("logs", [])[-6:]:
                print("   LOG:", line)
            break

print("\n3. Testing open-folder endpoint...")
open_req = urllib.request.Request(
    f"{base}/api/downloader/open-folder",
    data=json.dumps({"folder": "D:/SN_Dramas"}).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(open_req, timeout=5) as r:
    print("Open folder response:", r.read().decode())
