import sys
import urllib.request
import json
import sqlite3

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect("data/hongguo_catalog.db")
cur = conn.cursor()
cur.execute("SELECT title_cn FROM hongguo_dramas WHERE platform_id = 'ai_drama'")
existing_titles = set(row[0] for row in cur.fetchall())
conn.close()

print(f"Current AI dramas in database: {len(existing_titles):,}")

# Sample first 5 pages of Lzizy t=52
lzizy_samples = []
req = urllib.request.Request("https://cj.lziapi.com/api.php/provide/vod/?ac=detail&t=52&pg=1", headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=8) as res:
        data = json.loads(res.read().decode('utf-8'))
        items = data.get('list', [])
        new_cnt = sum(1 for it in items if (it.get('vod_name') or '').strip() not in existing_titles)
        print(f"Lzizy Page 1 items: {len(items)}, New unique titles not in DB: {new_cnt}")
        for it in items[:5]:
            name = (it.get('vod_name') or '').strip()
            print(f"  * {name} (In DB: {name in existing_titles}) - Stream: {(it.get('vod_play_url') or '')[:40]}")
except Exception as e:
    print("Error:", e)
