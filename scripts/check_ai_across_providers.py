import sys
import urllib.request
import json

sys.stdout.reconfigure(encoding='utf-8')

targets = [
    ("Baofen (t=74 AI漫剧)", "https://bfzyapi.com/api.php/provide/vod/?ac=list&t=74"),
    ("Lzizy (t=52 AI漫剧)", "https://cj.lziapi.com/api.php/provide/vod/?ac=list&t=52"),
    ("Guangsu (t=52 AI漫剧)", "https://api.guangsuapi.com/api.php/provide/vod/?ac=list&t=52"),
    ("Modu (t=42 AI漫剧)", "https://www.moduzy.com/api.php/provide/vod/?ac=list&t=42"),
]

headers = {'User-Agent': 'Mozilla/5.0'}

for name, url in targets:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as res:
            data = json.loads(res.read().decode('utf-8'))
            print(f"{name:<25} | Total: {data.get('total', 0):>6} dramas | Pages: {data.get('pagecount', 0)}")
    except Exception as e:
        print(f"{name} Error: {e}")
