import urllib.request
import urllib.parse
import json
import time

apis = [
    ("Modu", "https://www.moduzy.com/api.php/provide/vod/"),
    ("Wujin", "https://api.wujinapi.me/api.php/provide/vod/"),
    ("Guangsu", "https://api.guangsuapi.com/api.php/provide/vod/"),
    ("Baofen", "https://bfzyapi.com/api.php/provide/vod/"),
    ("Feifan", "http://cj.ffzyapi.com/api.php/provide/vod/"),
    ("Jinying", "https://jinyingzy.com/provide/vod/"),
    ("Yinghua", "https://m3u8.apiyhzy.com/api.php/provide/vod/"),
    ("Suoni", "https://suoniapi.com/api.php/provide/vod/"),
    ("Wolong", "https://collect.wolongzyw.com/api.php/provide/vod/")
]

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

test_word = "战神"

for name, base_url in apis:
    t0 = time.time()
    try:
        url = f"{base_url}?ac=detail&wd={urllib.parse.quote(test_word)}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=3.5) as r:
            raw = r.read()
            try:
                data = json.loads(raw.decode('utf-8', errors='ignore'))
                lst = data.get('list', [])
                print(f"[{name}] OK ({time.time()-t0:.2f}s) - Found {len(lst)} items. Sample: {lst[0].get('vod_name') if lst else 'None'}")
            except Exception as je:
                print(f"[{name}] Non-JSON ({time.time()-t0:.2f}s): {raw[:50]}")
    except Exception as e:
        print(f"[{name}] Failed ({time.time()-t0:.2f}s): {e}")
