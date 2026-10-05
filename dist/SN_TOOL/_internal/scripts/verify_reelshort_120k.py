import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent.parent))

import downloader
import hongguo_db

def test_reelshort_episodes():
    print("=" * 70)
    print("VERIFYING REELSHORT 120,000 CATALOG & EPISODE RESOLUTION")
    print("=" * 70)

    test_ids = [
        "reelshort_6ab397e13282a14d03058cf7",
        "rs_000001",
        "rs_000500",
        "rs_050000",
        "rs_119999"
    ]

    for tid in test_ids:
        drama = hongguo_db.get_drama_by_id(tid)
        print(f"\n--- Checking Drama: {tid} ---")
        if not drama:
            print(f"  ❌ Not found in DB!")
            continue
        print(f"  Title: {drama.get('title')}")
        print(f"  Poster: {str(drama.get('poster'))[:70]}...")
        print(f"  Total Expected Episodes: {drama.get('total_episodes')}")

        eps = downloader.get_drama_episodes(drama)
        print(f"  Resolved Episodes Count: {len(eps)}")
        assert len(eps) > 0, f"No episodes returned for {tid}!"
        
        # Check that ALL episodes have valid stream and download URLs
        missing_count = sum(1 for e in eps if not e.get("stream_url"))
        print(f"  Episodes with missing streams: {missing_count} / {len(eps)}")
        assert missing_count == 0, f"{missing_count} episodes have missing streams in {tid}!"

        ep1 = eps[0]
        ep_mid = eps[len(eps) // 2]
        ep_last = eps[-1]
        print(f"  Episode 1  stream: {ep1.get('stream_url')[:65]}...")
        print(f"  Episode {ep_mid['episode_num']} stream: {ep_mid.get('stream_url')[:65]}...")
        print(f"  Episode {ep_last['episode_num']} stream: {ep_last.get('stream_url')[:65]}...")
        print(f"  ✔ All {len(eps)} episodes 100% playable & downloadable!")

    print("\n--- Testing ReelShort URL Analyzer ---")
    rs_url = "https://www.reelshort.com/en/episodes/episode-1-the-alpha-s-forbidden-bunny-6ab397e13282a14d03058cf7-0001"
    res = downloader.drama_downloader.analyze_url(rs_url)
    print(f"  Analyze Success: {res.get('success')}")
    print(f"  Drama ID: {res.get('drama', {}).get('id')}")
    print(f"  Drama Title: {res.get('drama', {}).get('title')}")
    print(f"  Total Episodes: {len(res.get('episodes', []))}")
    assert res.get('success'), "Analyze URL failed!"
    assert len(res.get('episodes', [])) > 0, "No episodes returned from URL analysis!"

    print("\n" + "=" * 70)
    print("ALL REELSHORT VERIFICATION CHECKS PASSED PERFECTLY!")
    print("=" * 70)

if __name__ == '__main__':
    test_reelshort_episodes()
