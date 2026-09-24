import urllib.request
import urllib.parse
import json

apis = [
    ('Suoni', 'https://suoniapi.com/api.php/provide/vod/'),
    ('Wujin', 'https://api.wujinapi.me/api.php/provide/vod/'),
    ('Guangsu', 'https://api.guangsuapi.com/api.php/provide/vod/'),
    ('Modu', 'https://www.moduzy.com/api.php/provide/vod/')
]
for q in ['渔民直播', '渔网通宝库', '渔网', '心声藏不住', '裴总别装了']:
    print(f"\nQuery: {q}")
    for name, u in apis:
        try:
            req = urllib.request.Request(f"{u}?ac=detail&wd={urllib.parse.quote(q)}", headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=2.5) as r:
                d = json.loads(r.read().decode('utf-8', errors='ignore'))
                for item in d.get('list', []):
                    print(f"  [{name}] {item.get('vod_name')} ({len(item.get('vod_play_url', '').split('#'))} eps)")
        except Exception as e:
            pass
