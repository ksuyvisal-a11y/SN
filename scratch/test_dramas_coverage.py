import sys, yt_dlp, urllib.request, urllib.parse, json
sys.stdout.reconfigure(encoding='utf-8')

test_dramas = [
    "全家把我当乡下老太，都吓傻了",
    "糯糯下山，师兄们都慌了",
    "我的婆婆，我罩着",
    "暴富：山城故事",
    "东北婆婆，笑护全家",
    "盛总，太太只留孩子不留您"
]

apis = [
    ("Modu", "https://www.moduzy.com/api.php/provide/vod/"),
    ("Baofen", "https://bfzyapi.com/api.php/provide/vod/"),
    ("FFm3u8", "https://cj.ffzyapi.com/api.php/provide/vod/"),
    ("Lzizy", "https://cj.lziapi.com/api.php/provide/vod/"),
    ("Hongniu", "https://www.hongniuzy2.com/api.php/provide/vod/"),
    ("Guangsu", "https://api.guangsuapi.com/api.php/provide/vod/"),
    ("Uku", "https://api.ukuapi.com/api.php/provide/vod/"),
]

headers = {'User-Agent': 'Mozilla/5.0'}

for title in test_dramas:
    print(f"\n==========================================")
    print(f"Testing Drama: {title}")
    # 1. Test VOD clusters
    found_vod = False
    for name, base in apis:
        try:
            u = f"{base}?ac=detail&wd={urllib.parse.quote(title[:6])}"
            req = urllib.request.Request(u, headers=headers)
            with urllib.request.urlopen(req, timeout=3) as r:
                data = json.loads(r.read().decode('utf-8'))
                items = data.get('list', [])
                if items:
                    vname = items[0].get('vod_name', '')
                    play_url = items[0].get('vod_play_url', '')
                    eps_cnt = len(play_url.split('#')) if play_url else 0
                    print(f"  ✔ [VOD {name}] Found '{vname}' with {eps_cnt} episodes!")
                    found_vod = True
                    break
        except Exception:
            pass

    # 2. Test Online Full Series via yt-dlp if VOD not found or has few episodes
    if not found_vod:
        try:
            ydl_opts = {'quiet': True, 'extract_flat': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{title} 短剧 全集", download=False)
                entries = info.get('entries', [])
                if entries:
                    e = entries[0]
                    dur = e.get('duration') or 0
                    print(f"  ✔ [Online Full Series] Found '{e.get('title')}' (Duration: {dur//60} mins, ID: {e.get('id')})")
        except Exception as ex:
            print(f"  ❌ Online search error: {ex}")
