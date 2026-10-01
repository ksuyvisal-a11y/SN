import sys
import urllib.request
import json

sys.stdout.reconfigure(encoding='utf-8')

url = "https://cj.lziapi.com/api.php/provide/vod/?ac=detail&t=52&pg=1"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=10) as res:
    data = json.loads(res.read().decode('utf-8'))
    item = data.get('list', [])[0]
    print("Title:", item.get('vod_name'))
    print("Pic:", item.get('vod_pic'))
    print("Play from:", item.get('vod_play_from'))
    print("Play URL:", item.get('vod_play_url')[:300])
