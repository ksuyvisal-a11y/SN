import sys, re, json, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import yt_dlp
sys.stdout.reconfigure(encoding='utf-8')

VOD_APIS = [
    ("Modu", "https://www.moduzy.com/api.php/provide/vod/"),
    ("Lzizy", "https://cj.lziapi.com/api.php/provide/vod/"),
    ("Hongniu", "https://www.hongniuzy2.com/api.php/provide/vod/"),
    ("Guangsu", "https://api.guangsuapi.com/api.php/provide/vod/"),
    ("Uku", "https://api.ukuapi.com/api.php/provide/vod/"),
    ("Baofen", "https://bfzyapi.com/api.php/provide/vod/"),
    ("FFm3u8", "https://cj.ffzyapi.com/api.php/provide/vod/"),
    ("Jinying", "https://jinyingzy.com/provide/vod/"),
    ("Ikun", "https://ikunzyapi.com/api.php/provide/vod/")
]

def clean_title_for_search(raw_title: str) -> list:
    bracketed = re.findall(r'[《【（「『\[](.*?)[》】）」』\]]', raw_title)
    base = bracketed[0] if bracketed else raw_title
    clean = base.split(' - ')[0].split(' (')[0].strip()
    clean = re.sub(r'第[一二三四五六七八九十0-9]+[季部]', '', clean).strip()
    clean = re.sub(r'[\(（]?[全大]结局[\)）]?', '', clean).strip()
    clean = re.sub(r'[\(（]?全集[\)）]?', '', clean).strip()
    clean = re.sub(r'^[^\w\u4e00-\u9fff]+|[^\w\u4e00-\u9fff]+$', '', clean)
    queries = [clean]
    parts = [p.strip() for p in re.split(r'[：:，,！？!？、·\s\-_—]+', clean) if len(p.strip()) >= 2]
    for p in parts:
        if p not in queries:
            queries.append(p)
    return queries[:3]

def parse_vod_play_url(play_url_raw: str, api_name: str = "VOD"):
    if not play_url_raw:
        return []
    groups = play_url_raw.split('$$$')
    best_eps = []
    for g in groups:
        raw_eps = g.split('#')
        curr_eps = []
        for idx, ep_str in enumerate(raw_eps):
            ep_str = ep_str.strip()
            if not ep_str:
                continue
            m3u8_url = ""
            ep_title = f"Episode {idx+1:02d}"
            if '$' in ep_str:
                parts = ep_str.split('$')
                ep_title = parts[0].strip() or ep_title
                for p in parts[1:]:
                    p_clean = p.strip()
                    if p_clean.startswith('http') and ('.m3u8' in p_clean.lower() or '.mp4' in p_clean.lower()):
                        m3u8_url = p_clean
                        break
                if not m3u8_url and parts[-1].strip().startswith('http'):
                    m3u8_url = parts[-1].strip()
            elif ep_str.startswith('http'):
                m3u8_url = ep_str
            if m3u8_url:
                curr_eps.append({"ep_num": idx+1, "title": ep_title, "stream_url": m3u8_url, "source": api_name})
        if len(curr_eps) > len(best_eps) or ('.m3u8' in g.lower() and len(curr_eps) >= len(best_eps) * 0.9):
            best_eps = curr_eps
    return best_eps

def resolve_drama_stream_super(raw_title: str):
    queries = clean_title_for_search(raw_title)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    all_candidate_sets = []
    
    def fetch_api(api_name, base_url, q):
        try:
            u = f"{base_url}?ac=detail&wd={urllib.parse.quote(q)}"
            req = urllib.request.Request(u, headers=headers)
            with urllib.request.urlopen(req, timeout=3.0) as r:
                data = json.loads(r.read().decode('utf-8', errors='ignore'))
                items = data.get('list', [])
                if not items:
                    return []
                # Pick best item
                best_item = items[0]
                q_clean = q.lower().strip()
                for it in items:
                    vn = str(it.get('vod_name', '')).lower()
                    if vn == q_clean or q_clean in vn:
                        best_item = it
                        break
                return parse_vod_play_url(best_item.get('vod_play_url', ''), api_name)
        except Exception:
            return []

    # 1. Parallel search across 9 VOD APIs
    for q in queries:
        with ThreadPoolExecutor(max_workers=len(VOD_APIS)) as pool:
            futs = [pool.submit(fetch_api, name, base, q) for name, base in VOD_APIS]
            for f in as_completed(futs):
                res = f.result()
                if res:
                    all_candidate_sets.append(res)
        if any(len(s) >= 40 for s in all_candidate_sets):
            break

    if all_candidate_sets:
        all_candidate_sets.sort(key=lambda s: len(s), reverse=True)
        best_set = all_candidate_sets[0]
        # If we have a good multi-episode set (e.g. >= 10 episodes)
        if len(best_set) >= 10:
            return {"type": "episodes", "episodes": best_set, "source": best_set[0]["source"]}

    # 2. If VOD has only 1 episode OR 0 episodes, search Online Full Series via yt-dlp
    search_q = f"{queries[0]} 短剧 全集"
    try:
        ydl_opts = {'quiet': True, 'extract_flat': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch3:{search_q}", download=False)
            entries = info.get('entries', [])
            for e in entries:
                dur = e.get('duration') or 0
                title = e.get('title', '')
                if dur > 600 or '全集' in title or '1-' in title or '1~' in title:
                    return {
                        "type": "master_full_stream",
                        "stream_url": e.get('url'),
                        "title": title,
                        "duration_sec": dur,
                        "source": "Online Full Drama HD"
                    }
    except Exception as ex:
        pass

    # If VOD candidate set had 1 episode, return it as master full stream
    if all_candidate_sets:
        single_ep = all_candidate_sets[0][0]
        return {
            "type": "master_full_stream",
            "stream_url": single_ep["stream_url"],
            "title": f"{raw_title} (Full Series)",
            "source": single_ep["source"]
        }

    return {"type": "none"}

# Test across the 5 sample dramas
test_titles = [
    "《东北话事人》 - រឿងភាគពិសេស 东北话事人",
    "《全家把我当乡下老太，都吓傻了》 - រឿងភាគពិសេស 全家把我当乡下老太，都吓傻了",
    "《糯糯下山，师兄们都慌了第三季》 - រឿងភាគពិសេស 糯糯下山，师兄们都慌了第三季",
    "《我的婆婆，我罩着》 - រឿងភាគពិសេស 我的婆婆，我罩着",
    "《盛总，太太只留孩子不留您》 - រឿងភាគពិសេស 盛总，太太只留孩子不留您"
]

for t in test_titles:
    res = resolve_drama_stream_super(t)
    print(f"Title: {t[:30]}...")
    print(f"  Type: {res.get('type')}, Source: {res.get('source')}")
    if res.get('type') == 'episodes':
        print(f"  Episodes found: {len(res.get('episodes'))} eps, sample URL: {res['episodes'][0]['stream_url'][:60]}")
    elif res.get('type') == 'master_full_stream':
        print(f"  Master Full Stream: URL={res.get('stream_url')[:60]}, Duration={res.get('duration_sec', 0)//60} mins")
    else:
        print("  NO STREAM FOUND")
    print()
