import sys
import urllib.request
import json

sys.stdout.reconfigure(encoding='utf-8')

apis = [
    ("Baofen (bfzyapi)", "https://bfzyapi.com/api.php/provide/vod/?ac=list"),
    ("Lzizy (cj.lziapi)", "https://cj.lziapi.com/api.php/provide/vod/?ac=list"),
    ("FFm3u8 (cj.ffzyapi)", "https://cj.ffzyapi.com/api.php/provide/vod/?ac=list"),
    ("Guangsu (guangsuapi)", "https://api.guangsuapi.com/api.php/provide/vod/?ac=list"),
    ("Uku (ukuapi)", "https://api.ukuapi.com/api.php/provide/vod/?ac=list"),
    ("Modu (moduzy)", "https://www.moduzy.com/api.php/provide/vod/?ac=list")
]

headers = {'User-Agent': 'Mozilla/5.0'}

for name, url in apis:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode('utf-8'))
            total = data.get('total', 0)
            classes = data.get('class', [])
            ai_classes = [c for c in classes if any(k in c.get('type_name', '') for k in ['AI', '短剧', '微剧', '漫剧'])]
            print(f"=== {name} (Total VODs: {total:,}) ===")
            for c in ai_classes:
                print(f"   * [{c.get('type_id')}] {c.get('type_name')} (PID: {c.get('type_pid')})")
    except Exception as e:
        print(f"=== {name} Error: {e} ===")
