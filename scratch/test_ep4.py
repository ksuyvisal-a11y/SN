import urllib.request
import json
import time

headers = {"Content-Type": "application/json"}
# Test submit for series 7683196130645003288, episode 4
payload = {
    "series_ids": ["7683196130645003288"],
    "ranges": {"7683196130645003288": "4"},
    "quality": "1080p",
    "concurrency": 2,
    "series_at_once": 1
}

req = urllib.request.Request("http://127.0.0.1:8000/dl/submit", data=json.dumps(payload).encode('utf-8'), headers=headers)
with urllib.request.urlopen(req, timeout=10) as res:
    print("Submit response:", json.loads(res.read().decode('utf-8')))

for i in range(20):
    time.sleep(1)
    with urllib.request.urlopen("http://127.0.0.1:8000/dl/status", timeout=5) as res:
        d = json.loads(res.read().decode('utf-8'))
        ser = d.get('series', [])
        if ser:
            s0 = ser[0]
            print(f"[{i}] status: {s0.get('status')}, done: {s0.get('done')}/{s0.get('total')}")
            if s0.get('status') == 'done':
                print("Episode 4 downloaded successfully!")
                break
