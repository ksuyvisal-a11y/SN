import sys
import os
import re
import json
import sqlite3
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect("data/hongguo_catalog.db")
cur = conn.cursor()

# Sample 10 Hongguo, 10 ShortMax, 10 AI Dramas
cur.execute("SELECT id, title, title_cn, platform_id, poster FROM hongguo_dramas WHERE platform_id = 'hongguo' ORDER BY rank_num LIMIT 10")
hg_samples = cur.fetchall()

cur.execute("SELECT id, title, title_cn, platform_id, poster FROM hongguo_dramas WHERE platform_id = 'shortmax' LIMIT 10")
sm_samples = cur.fetchall()

cur.execute("SELECT id, title, title_cn, platform_id, poster FROM hongguo_dramas WHERE platform_id = 'ai_drama' ORDER BY RANDOM() LIMIT 15")
ai_samples = cur.fetchall()

conn.close()

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import downloader

print("=" * 60)
print("🔍 DIAGNOSTIC: Testing Drama Episode Resolution & Streams")
print("=" * 60)

def test_drama(d_row):
    did, title, title_cn, plat, poster = d_row
    drama_dict = {
        "id": did,
        "title": title,
        "title_cn": title_cn,
        "platform_id": plat,
        "poster": poster
    }
    try:
        eps = downloader.get_drama_episodes(drama_dict)
        has_streams = sum(1 for e in eps if e.get("stream_url"))
        ep1_stream = eps[0].get("stream_url", "") if eps else ""
        valid_stream = bool(ep1_stream and ep1_stream.startswith("http"))
        return {
            "id": did,
            "title": (title_cn or title)[:30],
            "plat": plat,
            "total_eps": len(eps),
            "stream_eps": has_streams,
            "valid": valid_stream,
            "sample_stream": ep1_stream[:60]
        }
    except Exception as e:
        return {
            "id": did,
            "title": (title_cn or title)[:30],
            "plat": plat,
            "error": str(e),
            "valid": False
        }

print("\n--- 1. Testing AI Dramas ---")
for s in ai_samples:
    res = test_drama(s)
    status = "✅ PASS" if res.get("valid") else "❌ FAIL"
    print(f"{status} [{res['plat']}] {res['id']:<16} | {res['title']:<25} | Eps: {res.get('total_eps', 0)} (Streams: {res.get('stream_eps', 0)}) | {res.get('sample_stream', '')}")

print("\n--- 2. Testing ShortMax Dramas ---")
for s in sm_samples:
    res = test_drama(s)
    status = "✅ PASS" if res.get("valid") else "❌ FAIL"
    print(f"{status} [{res['plat']}] {res['id']:<16} | {res['title']:<25} | Eps: {res.get('total_eps', 0)} (Streams: {res.get('stream_eps', 0)}) | {res.get('sample_stream', '')}")

print("\n--- 3. Testing Hongguo Dramas ---")
for s in hg_samples:
    res = test_drama(s)
    status = "✅ PASS" if res.get("valid") else "❌ FAIL"
    print(f"{status} [{res['plat']}] {res['id']:<16} | {res['title']:<25} | Eps: {res.get('total_eps', 0)} (Streams: {res.get('stream_eps', 0)}) | {res.get('sample_stream', '')}")
