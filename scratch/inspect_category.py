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

req = urllib.request.Request("https://hongguoduanju.com/category", headers=headers)
with urllib.request.urlopen(req, timeout=8) as res:
    html = res.read().decode('utf-8', errors='ignore')

m = re.search(r'_ROUTER_DATA\s*=\s*(\{.*?\});', html)
if m:
    data = json.loads(m.group(1))
    c_page = data.get("loaderData", {}).get("category_$", {})
    print("Category keys:", list(c_page.keys()))
    for k, v in c_page.items():
        if isinstance(v, list):
            print(f"List {k}: len={len(v)}")
            if len(v) > 0:
                print(f"  sample: {json.dumps(v[0], ensure_ascii=False)[:300]}")
        elif isinstance(v, dict):
            print(f"Dict {k}: subkeys={list(v.keys())}")
            print(f"  sample: {json.dumps(v, ensure_ascii=False)[:300]}")
        else:
            print(f"Val {k}: {v}")
