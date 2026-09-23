import sys
sys.stdout.reconfigure(encoding='utf-8')
import urllib.request
import json
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://hongguoduanju.com/',
    'Origin': 'https://hongguoduanju.com'
}

req = urllib.request.Request("https://hongguoduanju.com/", headers=headers)
with urllib.request.urlopen(req, timeout=8) as res:
    html = res.read().decode('utf-8', errors='ignore')

m = re.search(r'_ROUTER_DATA\s*=\s*(\{.*?\});', html)
if m:
    data = json.loads(m.group(1))
    print("Homepage loaderData keys:", list(data.get("loaderData", {}).keys()))
    for k, v in data.get("loaderData", {}).items():
        if isinstance(v, dict):
            print(f"Key: {k}, Subkeys: {list(v.keys())}")
            # print items or ranks
            for subk in v.keys():
                if isinstance(v[subk], (list, dict)):
                    print(f"  {subk}: len={len(v[subk])}")
                    if isinstance(v[subk], list) and len(v[subk]) > 0:
                        print(f"    sample[0]: {json.dumps(v[subk][0], ensure_ascii=False)[:200]}")
