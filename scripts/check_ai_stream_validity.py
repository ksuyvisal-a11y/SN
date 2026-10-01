import sys
import json
import sqlite3

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect("data/hongguo_catalog.db")
cur = conn.cursor()
cur.execute("SELECT id, title_cn FROM hongguo_dramas WHERE platform_id = 'ai_drama'")
ai_rows = cur.fetchall()
conn.close()

with open("data/ai_dramas_streams.json", "r", encoding="utf-8") as f:
    streams = json.load(f)

missing_stream = []
empty_stream = []
share_url_stream = []
valid_stream = []

for did, title in ai_rows:
    if did not in streams:
        missing_stream.append((did, title))
    else:
        purl = streams[did].get("play_url", "").strip()
        if not purl:
            empty_stream.append((did, title))
        elif "share/" in purl and ".m3u8" not in purl:
            share_url_stream.append((did, title, purl))
        else:
            valid_stream.append((did, title))

print(f"Total AI dramas in DB:       {len(ai_rows):,}")
print(f"Valid M3U8 streams:          {len(valid_stream):,}")
print(f"Missing from stream cache:   {len(missing_stream):,}")
print(f"Empty play_url in cache:     {len(empty_stream):,}")
print(f"Share page URL in cache:     {len(share_url_stream):,}")

if share_url_stream:
    print("\nSample share page URLs:")
    for did, t, u in share_url_stream[:5]:
        print(f"  {did} | {t} | {u}")
