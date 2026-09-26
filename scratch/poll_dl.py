import sys
sys.stdout.reconfigure(encoding='utf-8')
import urllib.request
import json
import time

for i in range(15):
    time.sleep(1)
    with urllib.request.urlopen('http://127.0.0.1:8000/dl/status', timeout=5) as res:
        d = json.loads(res.read().decode('utf-8'))
        print(f"[{i}] running: {d.get('running')}, phase: {d.get('phase')}")
        for l in d.get('log', [])[-3:]:
            print("   log:", l)
        series = d.get('series', [])
        if series:
            print("   series:", series)
        if not d.get('running') and i > 2:
            print("Download completed!")
            break
