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

test_urls = [
    "https://hongguoduanju.com/rank",
    "https://hongguoduanju.com/top",
    "https://hongguoduanju.com/channel",
    "https://hongguoduanju.com/category",
    "https://hongguoduanju.com/library"
]

for u in test_urls:
    try:
        req = urllib.request.Request(u, headers=headers)
        with urllib.request.urlopen(req, timeout=4) as res:
            html = res.read().decode('utf-8', errors='ignore')
            m = re.search(r'_ROUTER_DATA\s*=\s*(\{.*?\});', html)
            if m:
                data = json.loads(m.group(1))
                print(f"URL: {u} -> Status {res.status}, LoaderData: {list(data.get('loaderData', {}).keys())}")
            else:
                print(f"URL: {u} -> Status {res.status}, No router data")
    except Exception as e:
        print(f"URL: {u} -> Error: {e}")
