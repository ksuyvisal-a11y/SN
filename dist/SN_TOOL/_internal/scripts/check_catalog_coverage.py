import sys
import json
import sqlite3
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect("data/hongguo_catalog.db")
cur = conn.cursor()
cur.execute("SELECT id, title_cn, platform_id FROM hongguo_dramas")
all_dramas = cur.fetchall()
conn.close()

with open("data/ai_dramas_streams.json", "r", encoding="utf-8") as f:
    ai_streams = json.load(f)

with open("data/shortmax_all_dramas.json", "r", encoding="utf-8") as f:
    sm_data = json.load(f)
    if isinstance(sm_data, list):
        sm_dict = {str(d.get("id")): d for d in sm_data}
    else:
        sm_dict = sm_data

ai_missing = []
sm_missing = []
hg_count = 0

for did, title, plat in all_dramas:
    if plat == 'ai_drama':
        if did not in ai_streams:
            ai_missing.append((did, title))
    elif plat == 'shortmax':
        clean_id = did.replace("shortmax_", "")
        if clean_id not in sm_dict and did not in sm_dict:
            sm_missing.append((did, title))
    elif plat == 'hongguo':
        hg_count += 1

print(f"Total AI dramas in DB: {sum(1 for d in all_dramas if d[2] == 'ai_drama'):,}")
print(f"AI dramas missing from stream cache: {len(ai_missing):,}")
if ai_missing:
    print("Sample missing AI dramas:", ai_missing[:5])

print(f"\nTotal ShortMax dramas in DB: {sum(1 for d in all_dramas if d[2] == 'shortmax'):,}")
print(f"ShortMax missing from stream cache: {len(sm_missing):,}")

print(f"\nTotal Hongguo dramas in DB: {hg_count:,}")
