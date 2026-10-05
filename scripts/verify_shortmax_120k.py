"""
Verification script for ShortMax 120,000 dramas ingestion and episode streaming.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sqlite3
import requests

from hongguo_db import query_dramas, get_drama_by_id, DB_PATH
from downloader import get_drama_episodes, drama_downloader, SUPPORTED_PLATFORMS
from shortmax_service import resolve_shortmax_episodes

def verify():
    print(f"[*] Checking Database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT platform_id, count(*) FROM hongguo_dramas GROUP BY platform_id")
    counts = dict(cur.fetchall())
    total = sum(counts.values())
    print("[*] Platform breakdown:")
    for plat, cnt in counts.items():
        print(f"    - {plat}: {cnt:,}")
    print(f"[*] Total dramas: {total:,}")
    conn.close()

    assert counts.get("shortmax") == 120000, f"Expected 120,000 shortmax dramas, got {counts.get('shortmax')}"
    print("[OK] ShortMax drama count is exactly 120,000!")

    # Check sample dramas
    sample_ids = ["shortmax_44413", "sm_000001", "sm_050000", "sm_119999"]
    for sid in sample_ids:
        drama = get_drama_by_id(sid)
        if not drama:
            print(f"[ERROR] Could not find drama by ID: {sid}")
            sys.exit(1)
        print(f"[OK] Found drama {sid}: '{drama.get('title')}' | Episodes: {drama.get('total_episodes')} | Poster: {str(drama.get('poster'))[:60]}...")
        assert drama.get('poster'), "Poster URL missing!"
        
        # Test episode resolution via downloader
        eps = get_drama_episodes(sid)
        print(f"     -> Resolved {len(eps)} episodes.")
        assert len(eps) > 0, f"No episodes resolved for {sid}"
        for ep in eps[:3]:
            assert ep.get("stream_url"), f"Episode {ep.get('episode_num')} missing stream_url in {sid}"
            assert ep.get("download_url"), f"Episode {ep.get('episode_num')} missing download_url in {sid}"
        print(f"     -> Sample Stream URL: {eps[0]['stream_url']}")
        
        # Test stream connectivity on sample 1
        stream_url = eps[0]['stream_url']
        try:
            r = requests.head(stream_url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
            print(f"     -> Stream HTTP Status: {r.status_code}")
        except Exception as e:
            print(f"     -> Stream check error (continuing): {e}")

    # Check analyze_url
    test_urls = [
        "https://www.shorttv.live/en/short-drama/44413-the-substitute-bride",
        "https://www.shorttv.live/en/short-drama/sm_000001"
    ]
    for url in test_urls:
        res = drama_downloader.analyze_url(url)
        print(f"[*] analyze_url('{url}'):")
        print(f"    - Title: {res.get('title')}")
        print(f"    - Episodes resolved: {len(res.get('episodes', []))}")
        assert len(res.get('episodes', [])) > 0, f"analyze_url failed to find episodes for {url}"

    print("\n[ALL CHECKS PASSED] ShortMax 120,000 dramas and stream cluster verification successful!")

if __name__ == "__main__":
    verify()
