import urllib.request
import json
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
}

sid = '7684267771655359550'
url = f'https://hongguoduanju.com/detail?series_id={sid}'
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=5) as r:
    html = r.read().decode('utf-8', errors='ignore')

m = re.search(r'_ROUTER_DATA\s*=\s*(\{.*?\});', html)
if m:
    data = json.loads(m.group(1))
    dp = data['loaderData']['detail_page']
    sd = dp['seriesDetail']
    print('series_name:', sd.get('series_name'))
    print('accessible_episode_cnt:', sd.get('accessible_episode_cnt'))
    print('vid_list:', sd.get('vid_list')[:5])
    print('series_episode_info type:', type(sd.get('series_episode_info')))
    print('series_episode_info sample:', str(sd.get('series_episode_info'))[:300])
    vl = dp.get('videoList')
    print('videoList len:', len(vl) if vl else 0)
    if vl:
        print('videoList[0] keys:', list(vl[0].keys()))
        print('videoList[0]:', vl[0])
