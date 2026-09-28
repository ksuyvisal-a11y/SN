import urllib.request, urllib.parse, json, sys
sys.stdout.reconfigure(encoding='utf-8')
headers = {'User-Agent': 'Mozilla/5.0'}
test_apis = [
    ('Suoni', 'https://suoniapi.com/api.php/provide/vod/'),
    ('Wolong', 'https://wolongzyw.com/api.php/provide/vod/'),
    ('Lzizy', 'https://cj.lziapi.com/api.php/provide/vod/'),
    ('Hongniu', 'https://www.hongniuzy2.com/api.php/provide/vod/'),
    ('Guangsu', 'https://api.guangsuapi.com/api.php/provide/vod/'),
    ('Kuaikan', 'https://kuaikan-api.com/api.php/provide/vod/'),
    ('Uku', 'https://api.ukuapi.com/api.php/provide/vod/'),
    ('Wjm3u8', 'https://api.wujinapi.me/api.php/provide/vod/'),
]
for name, base in test_apis:
    try:
        u = f"{base}?ac=detail&wd={urllib.parse.quote('战神')}"
        req = urllib.request.Request(u, headers=headers)
        with urllib.request.urlopen(req, timeout=3.5) as r:
            data = json.loads(r.read().decode('utf-8'))
            cnt = len(data.get('list', []))
            print(f"{name}: OK ({cnt} items)")
    except Exception as e:
        print(f"{name}: Failed ({e})")
