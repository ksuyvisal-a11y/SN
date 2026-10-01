import sqlite3
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/hongguo_catalog.db')
cur = conn.cursor()

cur.execute("SELECT platform_id, COUNT(*) FROM hongguo_dramas GROUP BY platform_id")
counts = dict(cur.fetchall())
print("Total dramas per platform in DB:", counts)

# Load AI streams
with open('data/ai_dramas_streams.json', 'r', encoding='utf-8') as f:
    ai_streams = json.load(f)

print(f"Total stream records in ai_dramas_streams.json: {len(ai_streams)}")

# Build fast indexes
ai_id_set = set(ai_streams.keys())
for k in list(ai_streams.keys()):
    ai_id_set.add(k.replace("ai_", ""))

ai_title_set = set()
for k, v in ai_streams.items():
    if isinstance(v, dict):
        t = (v.get("title") or "").strip().lower()
        if t:
            ai_title_set.add(t)

# Check AI Drama coverage
cur.execute("SELECT id, title, title_cn FROM hongguo_dramas WHERE platform_id = 'ai_drama'")
ai_dramas = cur.fetchall()

ai_matched = 0
ai_unmatched = []
for did, t, t_cn in ai_dramas:
    did_str = str(did).strip()
    clean_t = (t_cn or t or "").strip().lower()
    if did_str in ai_id_set or clean_t in ai_title_set:
        ai_matched += 1
    else:
        ai_unmatched.append((did, t_cn or t))

print(f"AI Dramas matched in streams cache: {ai_matched} / {len(ai_dramas)} ({ai_matched/len(ai_dramas)*100:.2f}%)")
if ai_unmatched:
    print(f"Unmatched AI Dramas count: {len(ai_unmatched)}. Sample: {ai_unmatched[:5]}")

# Check ShortMax coverage
try:
    with open('data/shortmax_all_dramas.json', 'r', encoding='utf-8') as f:
        sm_data = json.load(f)
    print(f"Total ShortMax in JSON: {len(sm_data)}")
except Exception as e:
    print(f"ShortMax JSON check error: {e}")

# Check Hongguo ByteDance Series coverage
cur.execute("SELECT COUNT(*) FROM hongguo_dramas WHERE platform_id = 'hongguo' AND id LIKE 'hg_%'")
hg_vids_count = cur.fetchone()[0]
print(f"Hongguo dramas with hg_ series IDs: {hg_vids_count} / {counts.get('hongguo', 0)}")

# Check Hongguo matching AI cache
cur.execute("SELECT id, title, title_cn FROM hongguo_dramas WHERE platform_id = 'hongguo'")
hg_dramas = cur.fetchall()
hg_matched_ai = 0
for did, t, t_cn in hg_dramas:
    clean_t = (t_cn or t or "").strip().lower()
    if clean_t in ai_title_set:
        hg_matched_ai += 1
print(f"Hongguo dramas matching AI streams cache: {hg_matched_ai} / {len(hg_dramas)} ({hg_matched_ai/len(hg_dramas)*100:.2f}%)")

conn.close()
