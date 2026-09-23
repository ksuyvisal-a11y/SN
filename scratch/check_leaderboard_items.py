import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
req = urllib.request.Request('https://explorer.hongguodownloader.com/leaderboard?board=hot&category=all&size=100', headers={'User-Agent': 'Mozilla/5.0'})
data = json.loads(urllib.request.urlopen(req, timeout=10).read().decode('utf-8'))
items = data.get('items', [])
print(f'Total leaderboard items: {len(items)}')
for idx, i in enumerate(items[:20]):
    print(f"{idx+1}. {i.get('title')} | Score: {i.get('score')} | Heat: {i.get('heat')} | Cover: {i.get('cover')}")
