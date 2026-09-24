import urllib.request
import urllib.parse
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

test_query = "东北话事人"
encoded_query = urllib.parse.quote(test_query)

apis = [
    ("Liangzi", f"https://cj.lziapi.com/api.php/provide/vod/?ac=detail&wd={encoded_query}"),
    ("Feifan", f"https://ffzyapi.com/api.php/provide/vod/?ac=detail&wd={encoded_query}"),
    ("Baofeng", f"https://bfzyapi.com/api.php/provide/vod/?ac=detail&wd={encoded_query}"),
    ("Tiankong", f"https://api.tiankongapi.com/api.php/provide/vod/?ac=detail&wd={encoded_query}"),
    ("Suoni", f"https://suoniapi.com/api.php/provide/vod/?ac=detail&wd={encoded_query}"),
    ("Hongniu", f"https://hongniuzy2.com/api.php/provide/vod/?ac=detail&wd={encoded_query}"),
    ("iKun", f"https://ikunzyapi.com/api.php/provide/vod/?ac=detail&wd={encoded_query}"),
    ("Wwzy", f"https://api.wwzy.tv/api.php/provide/vod/?ac=detail&wd={encoded_query}")
]

headers = {'User-Agent': 'Mozilla/5.0'}

for name, url in apis:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as r:
            res_text = r.read().decode('utf-8', errors='ignore')
            data = json.loads(res_text)
            total = data.get('total')
            lst = data.get('list', [])
            print(f"[{name}] total={total} items={len(lst)}")
            if lst:
                for item in lst[:2]:
                    print(f"   Name: {item.get('vod_name')} (Type: {item.get('type_name')})")
                    play_url = item.get('vod_play_url', '')
                    eps = play_url.split('#')
                    print(f"   Episodes found: {len(eps)}")
                    if eps:
                        print(f"   First Ep: {eps[0][:100]}")
    except Exception as e:
        print(f"[{name}] failed: {e}")
