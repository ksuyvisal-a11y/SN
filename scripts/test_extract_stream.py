import sys
import urllib.request
import json

sys.stdout.reconfigure(encoding='utf-8')

def extract_best_m3u8_stream(play_from: str, play_url: str):
    if not play_url:
        return ""
    groups = play_url.split('$$$')
    from_names = play_from.split('$$$') if play_from else []
    
    # 1. Prefer group whose from_name contains 'm3u8'
    for idx, g in enumerate(groups):
        fname = from_names[idx].lower() if idx < len(from_names) else ""
        if 'm3u8' in fname and '.m3u8' in g:
            return g
            
    # 2. Prefer any group containing .m3u8
    for g in groups:
        if '.m3u8' in g:
            return g
            
    # 3. Fallback to longest group
    return max(groups, key=lambda g: len(g.split('#')))

# Test with 5 items from Lzizy
url = "https://cj.lziapi.com/api.php/provide/vod/?ac=detail&t=52&pg=1"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=10) as res:
    data = json.loads(res.read().decode('utf-8'))
    for it in data.get('list', [])[:5]:
        pfrom = it.get('vod_play_from', '')
        purl = it.get('vod_play_url', '')
        best = extract_best_m3u8_stream(pfrom, purl)
        print("Drama:", it.get('vod_name'))
        print("  From:", pfrom)
        print("  Best group preview:", best[:100])
        print("  Contains m3u8:", '.m3u8' in best)
