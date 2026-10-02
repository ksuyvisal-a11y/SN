import sys
import urllib.request
import urllib.parse
import json

sys.stdout.reconfigure(encoding='utf-8')
headers = {'User-Agent': 'Mozilla/5.0'}

apis = [
    ('Modu', 'https://caiji.modujx17.com/inc/apijson.php'),
    ('Lzizy', 'https://cj.lziapi.com/api.php/provide/vod/from/lzm3u8/'),
    ('Hongniu', 'https://www.hongniuzy2.com/api.php/provide/vod/from/hnm3u8/'),
    ('Guangsu', 'https://api.guangsuapi.com/api.php/provide/vod/from/gsm3u8/'),
    ('Uku', 'https://api.ukuapi.com/api.php/provide/vod/from/ukm3u8/'),
    ('Baofen', 'https://bfzyapi.com/api.php/provide/vod/from/bfm3u8/'),
    ('FFm3u8', 'https://cj.ffzyapi.com/api.php/provide/vod/from/ffm3u8/'),
    ('Jinying', 'https://jinyingzy.net/provide/vod/from/jinyingm3u8/'),
    ('Ikun', 'https://ikunzyapi.com/api.php/provide/vod/from/ikm3u8/')
]

queries = [
    '全家把我当乡下老太，都吓傻了',
    '全家把我当乡下老太',
    '都吓傻了',
    '乡下老太'
]

for q in queries:
    print(f'=== Testing Query: "{q}" ===')
    for name, api in apis:
        try:
            url = f'{api}?ac=detail&wd={urllib.parse.quote(q)}'
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode('utf-8', errors='ignore'))
                items = data.get('list', [])
                for it in items:
                    v_name = it.get('vod_name', '')
                    v_play = it.get('vod_play_url', '')
                    ep_cnt = len(v_play.split('#')) if v_play else 0
                    print(f'  [{name}] {v_name} -> {ep_cnt} episodes')
        except Exception as e:
            pass
