import urllib.request
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
headers = {'User-Agent': 'Mozilla/5.0'}
build_id = '1790563283648'

# Search book sample: 68b92154209a64e4bb0ed28a (Love & Blood)
bid = '68b92154209a64e4bb0ed28a'.strip()
slug = f'episode-1-love-blood-{bid}-0001'
url = f'https://www.reelshort.com/_next/data/{build_id}/en/episodes/{slug}.json?play_time=1&slug={slug}'

print(f"Testing resolution: {url}")
try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as r:
        d = json.loads(r.read().decode('utf-8'))
        fb = d.get('pageProps', {}).get('fallback', {})
        print("Fallback keys:", list(fb.keys()))
        for k, v in fb.items():
            if isinstance(v, dict):
                v_url = v.get('video_url') or v.get('play_url') or v.get('m3u8')
                if v_url:
                    print(f"Key {k} -> stream: {v_url}")
                if 'chapterList' in v or 'chapter_list' in v:
                    ch_list = v.get('chapterList') or v.get('chapter_list')
                    print(f"Key {k} -> chapter list count: {len(ch_list)}")
except Exception as e:
    print("Failed:", e)
