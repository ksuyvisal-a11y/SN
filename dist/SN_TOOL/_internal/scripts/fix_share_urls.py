import sys
import urllib.request
import json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ids = [138285, 128293, 127339]
streams_path = Path("data/ai_dramas_streams.json")
with open(streams_path, "r", encoding="utf-8") as f:
    streams = json.load(f)

for vid in ids:
    url = f"https://cj.lziapi.com/api.php/provide/vod/?ac=detail&ids={vid}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=8) as res:
            d = json.loads(res.read().decode('utf-8'))
            items = d.get('list', [])
            if items:
                it = items[0]
                pfrom = it.get('vod_play_from', '')
                purl = it.get('vod_play_url', '')
                groups = purl.split('$$$')
                froms = pfrom.split('$$$')
                print(f"VID {vid}: {it.get('vod_name')} | Froms: {froms}")
                m3u8_g = next((g for g in groups if '.m3u8' in g), "")
                if m3u8_g:
                    did = f"ai_lz_{vid}"
                    if did in streams:
                        streams[did]["play_url"] = m3u8_g
                        print(f"  ✔ Fixed {did} with real M3U8 group ({m3u8_g[:60]}...)")
                else:
                    print(f"  No m3u8 in groups for {vid}")
    except Exception as e:
        print(f"Error {vid}: {e}")

with open(streams_path, "w", encoding="utf-8") as f:
    json.dump(streams, f, ensure_ascii=False, indent=2)
print("Updated ai_dramas_streams.json!")
