def parse_vod_play_url(play_url_raw: str, api_name: str = "VOD"):
    if not play_url_raw:
        return []
    
    # If multiple server groups are separated by $$$, pick the best group (prefer m3u8)
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

sample_jinying = "全集完结$https://hd.kuktxu.com/play/dyPmMl7b$$$全集完结$https://hd.kuktxu.com/play/dyPmMl7b/index.m3u8"
sample_modu = "第01集$https://play.modu.com/ep1.m3u8#第02集$https://play.modu.com/ep2.m3u8"

print("Jinying parse:", parse_vod_play_url(sample_jinying, "Jinying"))
print("Modu parse:", parse_vod_play_url(sample_modu, "Modu"))
