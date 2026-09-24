import urllib.request
import re
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')
url = 'https://hongguoduanju.com/detail?series_id=7683196130645003288'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://hongguoduanju.com/'
}
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=10) as r:
    html = r.read().decode('utf-8', errors='ignore')

matches = re.findall(r'href=["\'](/player/[^"\']+)["\']', html)
print('Player hrefs count:', len(matches))
print('Player hrefs:', matches[:15])

m = re.search(r'_ROUTER_DATA\s*=\s*(\{.*?\});', html)
if m:
    data = json.loads(m.group(1))
    print('Router data keys:', list(data.keys()))
    loader = data.get('loaderData', {})
    print('loaderData keys:', list(loader.keys()))
    detail_page = loader.get('detail/page', {})
    print('detail/page keys:', list(detail_page.keys()))
    for k in detail_page:
        val = detail_page[k]
        if isinstance(val, (dict, list)):
            print(f"  {k}: type={type(val).__name__} len={len(val)}")
        else:
            print(f"  {k}: {val}")
