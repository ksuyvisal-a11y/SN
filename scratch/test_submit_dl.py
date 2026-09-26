import sys
sys.stdout.reconfigure(encoding='utf-8')
import urllib.request
import json

headers = {"Content-Type": "application/json"}
# Test submit for series 7683196130645003288, episodes 1
payload = {
    "series_ids": ["7683196130645003288"],
    "ranges": {"7683196130645003288": "1"},
    "quality": "1080p",
    "concurrency": 2,
    "series_at_once": 1
}

req = urllib.request.Request("http://127.0.0.1:8000/dl/submit", data=json.dumps(payload).encode('utf-8'), headers=headers)
try:
    with urllib.request.urlopen(req, timeout=10) as res:
        data = json.loads(res.read().decode('utf-8'))
        print("Submit response:", data)
except Exception as e:
    print("Submit error:", e)

# Check status
try:
    with urllib.request.urlopen("http://127.0.0.1:8000/dl/status", timeout=10) as res:
        status_data = json.loads(res.read().decode('utf-8'))
        print("\nStatus response:")
        print("  running:", status_data.get("running"))
        print("  phase:", status_data.get("phase"))
        print("  series:", status_data.get("series"))
        print("  log last 5:", status_data.get("log", [])[-5:])
except Exception as e:
    print("Status error:", e)
