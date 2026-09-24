import re
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional

VOD_APIS = [
    ("Modu", "https://www.moduzy.com/api.php/provide/vod/"),
    ("Hongniu", "https://hongniuzy2.com/api.php/provide/vod/")
]

def clean_drama_title_for_search(raw_title: str) -> str:
    """Clean drama title into pure searchable keywords."""
    if not raw_title:
        return ""
    t = raw_title
    t = re.sub(r'《(.*?)》', r'\1', t)
    t = t.split(' - ')[0]
    t = t.split(' (')[0]
    t = re.sub(r'[^\u4e00-\u9fff\w\s]', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def query_vod_stream_episodes(drama_title: str) -> List[Dict[str, Any]]:
    """Query VOD API cluster for real drama stream episodes."""
    query = clean_drama_title_for_search(drama_title)
    if not query:
        return []
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    for api_name, base_url in VOD_APIS:
        try:
            url = f"{base_url}?ac=detail&wd={urllib.parse.quote(query)}"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode('utf-8', errors='ignore'))
                items = data.get('list', [])
                if not items:
                    continue
                
                # Find best matching item
                matched_item = None
                for it in items:
                    v_name = it.get('vod_name', '')
                    if v_name == query or query in v_name or v_name in query:
                        matched_item = it
                        break
                if not matched_item:
                    matched_item = items[0]
                    
                play_url_raw = matched_item.get('vod_play_url', '')
                if not play_url_raw:
                    continue
                    
                episodes = []
                # Formats can be: 第01集$url#第02集$url OR url$$$url
                raw_eps = play_url_raw.split('#')
                for idx, ep_str in enumerate(raw_eps):
                    ep_str = ep_str.strip()
                    if not ep_str:
                        continue
                    m3u8_url = ""
                    ep_title = f"EP {idx+1:02d}"
                    if '$' in ep_str:
                        parts = ep_str.split('$')
                        ep_title = parts[0].strip() or ep_title
                        for p in parts[1:]:
                            if p.startswith('http') and ('.m3u8' in p or '.mp4' in p):
                                m3u8_url = p.strip()
                                break
                        if not m3u8_url and parts[-1].startswith('http'):
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
                        
                if episodes:
                    print(f"[{api_name}] Matched '{query}' -> '{matched_item.get('vod_name')}' with {len(episodes)} episodes!")
                    return episodes
        except Exception as e:
            print(f"[{api_name}] search failed for '{query}': {e}")
            
    return []

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    test_titles = [
        "《东北话事人》 - រឿងភាគពិសេស 东北话事人",
        "《糯糯下山，师兄们都慌了第三季》",
        "《无双神侯》",
        "《战神归乡：谁敢动我姐姐》",
        "《离婚后我独美，你哭什么》"
    ]
    for tt in test_titles:
        eps = query_vod_stream_episodes(tt)
        print(f"Result for {tt}: {len(eps)} episodes found. First: {eps[0] if eps else 'None'}\n")
