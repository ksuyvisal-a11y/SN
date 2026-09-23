import sys
sys.stdout.reconfigure(encoding='utf-8')
import urllib.request
import urllib.parse
import json
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://hongguoduanju.com/',
    'Origin': 'https://hongguoduanju.com'
}

u = "https://hongguoduanju.com/search?keyword=" + urllib.parse.quote("严禄")
req = urllib.request.Request(u, headers=headers)
with urllib.request.urlopen(req, timeout=5) as res:
    html = res.read().decode('utf-8', errors='ignore')

m = re.search(r'_ROUTER_DATA\s*=\s*(\{.*?\});', html)
if m:
    data = json.loads(m.group(1))
    sp = data.get("loaderData", {}).get("search_page", {})
    slist = sp.get("searchList", [])
    print(f"Total count: {sp.get('totalCount')}, searchList count: {len(slist)}")
    for item in slist[:3]:
        print("Item:", json.dumps(item, ensure_ascii=False)[:300])
else:
    print("No router data found")
