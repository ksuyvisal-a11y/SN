import sys
sys.stdout.reconfigure(encoding='utf-8')
import urllib.request
import json

headers = {"Content-Type": "application/json"}

# 1. Test POST /dl/resolve
print("--- Testing POST /dl/resolve ---")
try:
    payload = json.dumps({"url": "7683196130645003288"}).encode('utf-8')
    req = urllib.request.Request("http://127.0.0.1:8000/dl/resolve", data=payload, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as res:
        data = json.loads(res.read().decode('utf-8'))
        print("POST /dl/resolve success!")
        print("  Keys:", list(data.keys()))
        print("  Title:", data.get("title"))
        print("  Episodes:", len(data.get("episodes", [])))
        if "episodes" in data and data["episodes"]:
            print("  EP 1 details:", data["episodes"][0])
except Exception as e:
    print("POST /dl/resolve error:", e)

# 2. Inspect /dl/config
print("\n--- Testing GET /dl/config ---")
try:
    with urllib.request.urlopen("http://127.0.0.1:8000/dl/config", timeout=10) as res:
        data = json.loads(res.read().decode('utf-8'))
        print("Config:", data)
except Exception as e:
    print("Config error:", e)

# 3. Inspect /dl/status
print("\n--- Testing GET /dl/status ---")
try:
    with urllib.request.urlopen("http://127.0.0.1:8000/dl/status", timeout=10) as res:
        data = json.loads(res.read().decode('utf-8'))
        print("Status keys:", list(data.keys()))
        print("  Downloads in status:", len(data.get("downloads", [])))
except Exception as e:
    print("Status error:", e)
