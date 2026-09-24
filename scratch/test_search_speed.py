import time
import urllib.request
import urllib.parse
import json

queries = [
    '心声藏不住',
    '裴总别装了',
    '渔民直播',
    '渔网通宝库',
    '致命团建日',
    '熊猫嫡女的动物护卫',
    '动物护卫',
    '熊猫'
]
for q in queries:
    t0 = time.time()
    url = f'https://www.moduzy.com/api.php/provide/vod/?ac=detail&wd={urllib.parse.quote(q)}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8', errors='ignore'))
            lst = data.get('list', [])
            names = [x.get('vod_name') for x in lst[:3]]
            print(f'{q}: found {len(lst)} items -> {names} in {time.time()-t0:.2f}s')
    except Exception as e:
        print(f'{q}: Error {e} in {time.time()-t0:.2f}s')
