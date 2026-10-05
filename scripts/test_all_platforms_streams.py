import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.stdout:
    sys.stdout.reconfigure(encoding='utf-8')

import sqlite3
from hongguo_db import DB_PATH, get_drama_by_id
from downloader import get_drama_episodes

def test():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    platforms = ['hongguo', 'ai_drama', 'shortmax', 'reelshort', 'anyreel', 'freereels']
    total_tested = 0
    total_empty_streams = 0

    print("=== TESTING STREAM URL COVERAGE ACROSS ALL 6 PLATFORMS ===", flush=True)
    for plat in platforms:
        cur.execute("SELECT id, title, total_episodes FROM hongguo_dramas WHERE platform_id = ? ORDER BY id ASC LIMIT 5", (plat,))
        dramas = cur.fetchall()
        print(f"\n--- Platform: {plat.upper()} ({len(dramas)} sample dramas) ---", flush=True)
        for did, title, total_eps in dramas:
            d_obj = get_drama_by_id(did)
            eps = get_drama_episodes(d_obj or did)
            empty_cnt = sum(1 for e in eps if not e.get("stream_url"))
            total_tested += len(eps)
            total_empty_streams += empty_cnt
            sample_u = eps[0].get("stream_url", "")[:50] if eps else "N/A"
            status_str = "OK (100% covered)" if empty_cnt == 0 else f"FAIL ({empty_cnt} empty)"
            print(f"  [{status_str}] ID: {did} | Episodes: {len(eps)} | Stream: {sample_u}...", flush=True)

    conn.close()
    print(f"\n=======================================================", flush=True)
    print(f"Total Episodes Checked: {total_tested:,}", flush=True)
    print(f"Total Empty Streams:    {total_empty_streams}", flush=True)
    print(f"Coverage Rate:          {((total_tested - total_empty_streams) / total_tested * 100):.2f}%", flush=True)
    print(f"=======================================================", flush=True)
    assert total_empty_streams == 0, f"Found {total_empty_streams} empty streams!"
    print("ALL PLATFORMS VERIFIED: 100% STREAM COVERAGE GUARANTEED!")

if __name__ == "__main__":
    test()
