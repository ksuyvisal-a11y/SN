import urllib.request
import urllib.parse
import json
import re
import yt_dlp
import time
from typing import Dict, Any, List

# Only fast APIs (< 2 seconds)
SHORT_DRAMA_VOD_APIS = [
    ("Modu", "https://www.moduzy.com/api.php/provide/vod/"),
    ("Jinying", "https://jinyingzy.com/provide/vod/"),
    ("Baofen", "https://bfzyapi.com/api.php/provide/vod/")
]

def get_search_queries_for_title_v2(raw_title: str) -> List[str]:
    if not raw_title:
        return []
    candidates = []

    def add_cand(c: str):
        c = c.strip()
        c = re.sub(r'^[^\w\u4e00-\u9fff]+|[^\w\u4e00-\u9fff]+$', '', c)
        if c and len(c) >= 2 and c not in candidates:
            candidates.append(c)

    bracketed = re.findall(r'[《【（「『\[](.*?)[》】）」』\]]', raw_title)
    base_titles = bracketed if bracketed else [raw_title]

    for base in base_titles:
        clean = base.split(' - ')[0].split(' (')[0].strip()
        clean_no_season = re.sub(r'第[一二三四五六七八九十0-9]+[季部]', '', clean).strip()
        clean_no_season = re.sub(r'[\(（]?[全大]结局[\)）]?', '', clean_no_season).strip()
        clean_no_season = re.sub(r'[\(（]?全集[\)）]?', '', clean_no_season).strip()
        add_cand(clean_no_season)

        parts = [p.strip() for p in re.split(r'[：:，,！？!？、·\s\-_—]+', clean_no_season) if p.strip()]
        for p in parts:
            if len(p) >= 2:
                add_cand(p)

        ch_chars = "".join(re.findall(r'[\u4e00-\u9fff]', clean_no_season))
        if len(ch_chars) >= 4:
            add_cand(ch_chars[:4])
            if len(ch_chars) >= 6:
                add_cand(ch_chars[:5])
        elif len(ch_chars) >= 2:
            add_cand(ch_chars)

    return candidates[:4]  # Top 4 most relevant queries to keep it fast

def parse_vod_play_url(play_url_raw: str, api_name: str = "VOD") -> List[Dict[str, Any]]:
    if not play_url_raw:
        return []
    groups = play_url_raw.split('$$$')
    best_group = groups[0]
    for g in groups:
        if '.m3u8' in g.lower():
            best_group = g
            break
            
    episodes = []
    raw_eps = best_group.split('#')
    for idx, ep_str in enumerate(raw_eps):
        ep_str = ep_str.strip()
        if not ep_str:
            continue
        m3u8_url = ""
        ep_title = f"ភាគ {idx+1:02d}"
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
            episodes.append({
                "episode_num": idx + 1,
                "episode_number": idx + 1,
                "title": ep_title,
                "stream_url": m3u8_url,
                "source": api_name
            })
    return episodes

def resolve_streams_v2(raw_title: str) -> List[Dict[str, Any]]:
    queries = get_search_queries_for_title_v2(raw_title)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    best_episodes: List[Dict[str, Any]] = []

    for q in queries:
        for api_name, base_url in SHORT_DRAMA_VOD_APIS:
            try:
                url = f"{base_url}?ac=detail&wd={urllib.parse.quote(q)}"
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=2.0) as resp:
                    data = json.loads(resp.read().decode('utf-8', errors='ignore'))
                    items = data.get('list', [])
                    if not items:
                        continue
                    matched = None
                    for it in items:
                        vn = it.get('vod_name', '')
                        if vn == q or q in vn or vn in q:
                            matched = it
                            break
                    if not matched:
                        matched = items[0]

                    play_url = matched.get('vod_play_url', '')
                    eps = parse_vod_play_url(play_url, api_name)
                    if len(eps) > len(best_episodes):
                        best_episodes = eps
                        if len(best_episodes) > 5:
                            return best_episodes
            except Exception:
                pass

    if best_episodes:
        return best_episodes

    # Fallback to online search engine via yt-dlp
    search_q = f"ytsearch1:{queries[0]} 短剧" if queries else ""
    if search_q:
        try:
            ydl_opts = {'quiet': True, 'extract_flat': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search_q, download=False)
                entries = info.get('entries', [])
                if entries and entries[0].get('url'):
                    best_episodes = [{
                        "episode_num": 1,
                        "episode_number": 1,
                        "title": entries[0].get('title', 'Full Drama'),
                        "stream_url": entries[0].get('url'),
                        "source": "OnlineStream"
                    }]
        except Exception:
            pass

    return best_episodes

test_titles = [
    '《心声藏不住：裴总别装了》 - រឿងភាគ 心声藏不住：裴总别装了',
    '《渔民直播：我的渔网通宝库!》 - រឿងភាគ 渔民直播：我的渔网通宝库!',
    '《致命团建日》 - រឿងភាគ 致命团建日',
    '《东北话事人》',
    '《战神归乡：谁敢动我姐姐》'
]

for t in test_titles:
    t0 = time.time()
    eps = resolve_streams_v2(t)
    dt = time.time() - t0
    source = eps[0]['source'] if eps else 'None'
    print(f"[{dt:.2f}s] {t} -> {len(eps)} eps ({source})")
