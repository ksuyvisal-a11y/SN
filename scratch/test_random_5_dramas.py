import os
import sys
import random
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import hongguo_db
import downloader

def test_random_dramas():
    dramas, total = hongguo_db.query_dramas(limit=100)
    print(f"Total catalog count: {total}")
    sample_dramas = random.sample(dramas, 5)
    
    for idx, d in enumerate(sample_dramas, 1):
        title = d.get("title_cn") or d.get("title")
        sid = d.get("series_id") or d.get("id")
        print(f"\n[{idx}/5] Testing Drama: '{title}' (Series ID: {sid})")
        
        eps = downloader.get_drama_episodes(d)
        print(f"  Episodes generated: {len(eps)}")
        urls = [e.get("stream_url") or e.get("download_url") for e in eps if e.get("stream_url") or e.get("download_url")]
        print(f"  Playable stream URLs: {len(urls)} / {len(eps)}")
        if urls:
            print(f"  Sample stream 1: {urls[0][:70]}...")
            print(f"  Source: {eps[0].get('source')}")

if __name__ == "__main__":
    test_random_dramas()
