import urllib.request
import urllib.parse
import json
import time

apis = [
    ("Suoni", "https://suoniapi.com/api.php/provide/vod/"),
    ("Wujin", "https://api.wujinapi.me/api.php/provide/vod/"),
    ("Guangsu", "https://api.guangsuapi.com/api.php/provide/vod/"),
    ("Baofen", "https://bfzyapi.com/api.php/provide/vod/"),
    ("Modu", "https://www.moduzy.com/api.php/provide/vod/")
]

headers = {'User-Agent': 'Mozilla/5.0'}

test_dramas = [
    '心声藏不住',
    '裴总别装了',
    '渔网通宝库',
    '致命团建日',
    '东北话事人',
    '战神归乡',
    '无双神侯',
    '双生千金',
    '老太',
    '熊猫嫡女'
]

for title in test_dramas:
    print(f"\n--- Searching: {title} ---")
    for name, base_url in apis:
        t0 = time.time()
        try:
            url = f"{base_url}?ac=detail&wd={urllib.parse.quote(title)}"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=2.5) as r:
                data = json.loads(r.read().decode('utf-8', errors='ignore'))
                items = data.get('list', [])
                if items:
                    first = items[0]
                    vod_name = first.get('vod_name')
                    eps_count = len(first.get('vod_play_url', '').split('#'))
                    print(f"  [{name}] ({time.time()-t0:.2f}s) FOUND: {vod_name} ({eps_count} eps)")
                    # Print first ep url
                    sample_url = first.get('vod_play_url', '').split('#')[0]
                    # print(f"    sample: {sample_url[:60]}")
                    break
        except Exception as e:
            # print(f"  [{name}] failed: {e}")
            pass
