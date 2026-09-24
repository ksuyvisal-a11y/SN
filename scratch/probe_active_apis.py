import urllib.request
import json
import time

apis = [
    ("Modu", "https://www.moduzy.com/api.php/provide/vod/"),
    ("Hongniu", "https://hongniuzy2.com/api.php/provide/vod/"),
    ("Feifan", "http://cj.ffzyapi.com/api.php/provide/vod/"),
    ("Liangzi", "https://api.lz-api.com/api.php/provide/vod/"),
    ("Baofen", "https://bfzyapi.com/api.php/provide/vod/"),
    ("Suoni", "https://suoniapi.com/api.php/provide/vod/"),
    ("Tiankong", "https://api.tiankongapi.com/api.php/provide/vod/"),
    ("Wujin", "https://api.wujinapi.me/api.php/provide/vod/"),
    ("Kuaikan", "https://kuaikanzy.net/api.php/provide/vod/"),
    ("Jinying", "https://jinyingzy.com/provide/vod/"),
    ("Guangsu", "https://api.guangsuapi.com/api.php/provide/vod/"),
    ("Yinghua", "https://m3u8.apiyhzy.com/api.php/provide/vod/"),
    ("Wolong2", "https://collect.wolongzyw.com/api.php/provide/vod/")
]

headers = {'User-Agent': 'Mozilla/5.0'}

test_titles = ['东北话事人', '战神归乡', '无双神侯', '双生千金', '致命团建日']

for name, base_url in apis:
    t0 = time.time()
    try:
        url = f"{base_url}?ac=list"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=3) as r:
            data = json.loads(r.read().decode('utf-8', errors='ignore'))
            total = data.get('total', 0)
            class_list = [c.get('type_name') for c in data.get('class', []) if '短剧' in c.get('type_name', '')]
            dt = time.time() - t0
            print(f"[{name}] OK ({dt:.2f}s) - Total: {total} items | Short drama classes: {class_list}")
    except Exception as e:
        print(f"[{name}] Failed ({time.time()-t0:.2f}s): {e}")
