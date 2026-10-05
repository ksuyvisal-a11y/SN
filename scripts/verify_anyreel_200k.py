import sys
import os
import json
import sqlite3
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent.parent))

def verify_all():
    print("=" * 70)
    print("VERIFYING ANYREEL 200,000 CATALOG & DOWNLOAD COMPATIBILITY")
    print("=" * 70)

    # 1. DB count check
    conn = sqlite3.connect("data/hongguo_catalog.db")
    cur = conn.cursor()
    cur.execute("SELECT platform_id, count(*) FROM hongguo_dramas GROUP BY platform_id")
    rows = cur.fetchall()
    print("Platform breakdown in DB:")
    for p_id, count in rows:
        print(f"  - {p_id}: {count:,} dramas")
    
    cur.execute("SELECT count(*) FROM hongguo_dramas")
    total = cur.fetchone()[0]
    print(f"Total dramas in DB: {total:,}")
    assert total >= 404601, f"Expected at least 404,601 dramas, got {total}"
    
    cur.execute("SELECT count(*) FROM hongguo_dramas WHERE platform_id = 'anyreel'")
    ar_cnt = cur.fetchone()[0]
    assert ar_cnt == 200000, f"Expected 200,000 AnyReel dramas, got {ar_cnt}"
    print(f"✔ AnyReel drama count verified: {ar_cnt:,}")

    # Check sample posters
    cur.execute("SELECT id, title, poster FROM hongguo_dramas WHERE platform_id = 'anyreel' LIMIT 5")
    sample_records = cur.fetchall()
    print("\nSample AnyReel records in DB:")
    for r in sample_records:
        print(f"  ID: {r[0]} | Title: {r[1]} | Poster: {r[2][:70]}...")
    conn.close()

    # 2. Episode stream resolver check
    import downloader
    print("\nTesting episode stream resolution for sample AnyReel dramas:")
    test_ids = ["ar_000001", "ar_000500", "ar_050000", "ar_199999"]
    for tid in test_ids:
        drama_obj = downloader.hongguo_db.get_drama_by_id(tid)
        eps = downloader.get_drama_episodes(tid, drama_obj=drama_obj)
        print(f"  - {tid} ('{drama_obj['title'][:35]}...'): resolved {len(eps)} episodes")
        assert len(eps) > 0, f"No episodes resolved for {tid}"
        ep1 = eps[0]
        assert ep1.get("stream_url"), f"Episode 1 has no stream_url for {tid}!"
        assert ep1.get("download_url"), f"Episode 1 has no download_url for {tid}!"
        print(f"    EP 1 Stream URL: {ep1['stream_url'][:65]}... (Status: {ep1['status']})")

    # 3. Live video download test of 1 AnyReel episode
    print("\nTesting real live download of AnyReel episode 1:")
    d_loc = "scratch/test_dl_verify"
    d_dir = Path(d_loc)
    d_dir.mkdir(parents=True, exist_ok=True)
    
    test_d = downloader.hongguo_db.get_drama_by_id("ar_000001")
    downloader.drama_downloader.current_drama = test_d
    eps = downloader.get_drama_episodes("ar_000001", drama_obj=test_d)
    downloader.drama_downloader.episodes = eps
    
    ep_to_dl = eps[0]
    stream_u = ep_to_dl.get("stream_url")
    dest_file = d_dir / "ar_verify_ep1.mp4"
    if dest_file.exists():
        dest_file.unlink()

    print(f"  Downloading from stream: {stream_u[:60]}...")
    res = downloader.download_m3u8_stream_turbo(stream_u, dest_file, timeout_sec=60)
    print(f"  Download result: {res}")
    assert dest_file.exists(), "Target file does not exist!"
    sz_mb = dest_file.stat().st_size / (1024 * 1024)
    print(f"  ✔ Target file downloaded: {dest_file.name} ({sz_mb:.2f} MB)")
    assert sz_mb > 0.5, f"File size too small: {sz_mb} MB"

    print("\n" + "=" * 70)
    print("ALL VERIFICATION CHECKS PASSED PERFECTLY!")
    print("=" * 70)

if __name__ == '__main__':
    verify_all()
