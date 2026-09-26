import sys
sys.stdout.reconfigure(encoding='utf-8')
import urllib.request
import urllib.parse
import json

SHORT_DRAMA_VOD_APIS = [
    ("Jinying", "https://jinyingzy.com/provide/vod/"),
    ("Baofen", "https://bfzyapi.com/api.php/provide/vod/"),
    ("FFm3u8", "https://cj.ffzyapi.com/api.php/provide/vod/"),
    ("Modu", "https://www.moduzy.com/api.php/provide/vod/"),
    ("Ikun", "https://ikunzyapi.com/api.php/provide/vod/")
]

headers = {'User-Agent': 'Mozilla/5.0'}

test_titles = [
    '糯糯下山，师兄们都慌了第三季',
    '东北话事人',
    '全家把我当乡下老太，都吓傻了',
    '我的婆婆，我罩着',
    '暴富：山城故事3'
]

for title in test_titles:
    print(f"\n==========================================")
    print(f"Testing title: {title}")
    for api_name, base_url in SHORT_DRAMA_VOD_APIS:
        url = f"{base_url}?ac=detail&wd={urllib.parse.quote(title)}"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode('utf-8', errors='ignore'))
                items = data.get('list', [])
                if items:
                    it0 = items[0]
                    vod_name = it0.get('vod_name', '')
                    play_url = it0.get('vod_play_url', '')
                    eps_count = len(play_url.split('#')) if play_url else 0
                    print(f"  [{api_name}] MATCH: '{vod_name}' with {eps_count} episodes")
                else:
                    print(f"  [{api_name}] No match")
        except Exception as e:
            print(f"  [{api_name}] Error: {e}")
