import sys
import urllib.request
import json
import time

sys.stdout.reconfigure(encoding='utf-8')

t0 = time.time()
url = "https://cj.lziapi.com/api.php/provide/vod/?ac=detail&t=52&pg=1"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=5) as res:
    data = json.loads(res.read().decode('utf-8'))
    items = data.get('list', [])
    print(f"Fetched {len(items)} items in {time.time()-t0:.2f}s")
    if items:
        it = items[0]
        print("Sample:", it.get('vod_name'), "| vod_id:", it.get('vod_id'))
