import urllib.request
import json
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
}

sid = '7684267771655359550'
vids = ['7684306002035887166', '7684305993798257726', '7684306022315330622', '7684306031563787326', '7684305977671158846']

for idx, vid in enumerate(vids):
    url = f"https://hongguoduanju.com/player/{sid}/{vid}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as r:
            html = r.read().decode('utf-8', errors='ignore')
        m = re.search(r'_ROUTER_DATA\s*=\s*(\{.*?\});', html)
        if m:
            data = json.loads(m.group(1))
            page_data = data.get("loaderData", {}).get("player_(series_id)/(vid)/page", {})
            v_info = page_data.get("video_player_info", {})
            main_url = v_info.get("main_url")
            print(f'EP {idx+1} (VID {vid}): main_url = {main_url[:60] if main_url else "None"}')
            if not main_url:
                print('  page_data keys:', list(page_data.keys()))
                print('  video_player_info:', v_info)
    except Exception as e:
        print(f'EP {idx+1} error:', e)
