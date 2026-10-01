import json
import sqlite3
import random
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("Verifying 4,700 ReelShort Dramas Integrity & Downloadability")
print("=" * 60)

# Check JSON
with open("data/reelshort_all_dramas.json", "r", encoding="utf-8") as f:
    dramas = json.load(f)

print(f"Total dramas in JSON: {len(dramas)}")

# Check DB
conn = sqlite3.connect("data/hongguo_catalog.db")
cur = conn.cursor()
cur.execute("SELECT count(*) FROM hongguo_dramas WHERE platform_id = 'reelshort'")
db_cnt = cur.fetchone()[0]
print(f"Total ReelShort dramas in DB: {db_cnt}")

# Check 5 random dramas from the newly discovered pool
random.seed(42)
samples = random.sample(dramas, 5)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import downloader
import reelshort_service

for idx, d in enumerate(samples):
    print(f"\n[Sample {idx+1}] ID: {d['book_id']} | Title: {d['title']}")
    print(f"   Poster: {d['poster'][:60]}...")
    print(f"   Episodes Count: {d['chapter_count']}")
    
    # Test episode resolution via downloader
    drama_row = {
        'id': f"reelshort_{d['book_id']}",
        'book_id': d['book_id'],
        'title': d['title'],
        'platform': 'ReelShort',
        'platform_id': 'reelshort',
        'total_episodes': d['chapter_count'],
        'poster': d['poster'],
        'description': d['description']
    }
    eps = downloader.get_drama_episodes(drama_row)
    print(f"   Episodes generated: {len(eps)}")
    if eps:
        ep1 = eps[0]
        print(f"   EP1 ID: {ep1['id']}")
        print(f"   EP1 Stream URL: {ep1['stream_url'][:70]}...")
        print(f"   EP1 Status: {ep1['status']}")

print("\n--- Testing Live Episode 1 Stream URL Fetch on Sample 1 ---")
s1 = samples[0]
slug = s1.get('slug')
print(f"Slug: {slug}")
import reelshort_service
stream_info = reelshort_service.resolve_reelshort_stream(s1['book_id'], 1, slug)
print(f"Resolved Stream: {stream_info}")

conn.close()
