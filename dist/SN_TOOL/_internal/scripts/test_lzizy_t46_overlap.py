import sys
import urllib.request
import json
import sqlite3

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect("data/hongguo_catalog.db")
cur = conn.cursor()
cur.execute("SELECT title_cn FROM hongguo_dramas WHERE platform_id = 'ai_drama'")
ai_titles = set(r[0] for r in cur.fetchall())
conn.close()

print(f"Current AI Dramas in catalog: {len(ai_titles):,}")

url = "https://cj.lziapi.com/api.php/provide/vod/?ac=detail&t=46&pg=1"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=8) as res:
    data = json.loads(res.read().decode('utf-8'))
    items = data.get('list', [])
    new_in_ai = sum(1 for it in items if (it.get('vod_name') or '').strip() not in ai_titles)
    print(f"Lzizy t=46 Page 1 items: {len(items)}, New unique items not in AI Dramas: {new_in_ai}")
    for it in items[:5]:
        print("  -", it.get('vod_name'), "| in AI:", (it.get('vod_name') or '').strip() in ai_titles)
