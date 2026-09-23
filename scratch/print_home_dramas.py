import sys
sys.stdout.reconfigure(encoding='utf-8')
import urllib.request
import json
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://hongguoduanju.com/',
    'Origin': 'https://hongguoduanju.com'
}

req = urllib.request.Request("https://hongguoduanju.com/", headers=headers)
with urllib.request.urlopen(req, timeout=8) as res:
    html = res.read().decode('utf-8', errors='ignore')

m = re.search(r'_ROUTER_DATA\s*=\s*(\{.*?\});', html)
if m:
    data = json.loads(m.group(1))
    page = data.get("loaderData", {}).get("page", {})
    home_sections = page.get("homeSections", [])
    all_series = []
    for sec in home_sections:
        tname = sec.get("tab_name")
        vlist = sec.get("video_list", [])
        print(f"Section: {tname} -> {len(vlist)} dramas")
        for v in vlist:
            all_series.append((v.get("series_id"), v.get("series_title"), v.get("episode_cnt")))
            print(f"   {v.get('series_id')} | {v.get('series_title')} ({v.get('episode_cnt')} eps)")
    print(f"Total homepage dramas: {len(all_series)}")
