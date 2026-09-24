import os
import sys
import time
from pathlib import Path

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from downloader import (
    resolve_short_drama_stream_cluster,
    get_drama_episodes,
    download_m3u8_stream_with_ffmpeg,
    drama_downloader
)
import hongguo_db

def test_stream_cluster_resolution():
    print("=" * 60)
    print("1. TESTING SHORT DRAMA VOD CLUSTER RESOLUTION")
    print("=" * 60)
    
    test_dramas = [
        {"title": "《东北话事人》", "title_cn": "东北话事人"},
        {"title": "《糯糯下山，师兄们都慌了第三季》", "title_cn": "糯糯下山，师兄们都慌了"},
        {"title": "《无双神侯》", "title_cn": "无双神侯"},
        {"title": "《战神归乡：谁敢动我姐姐》", "title_cn": "战神归乡：谁敢动我姐姐"}
    ]
    
    for d in test_dramas:
        eps = get_drama_episodes(d)
        print(f"Drama: {d['title']} -> Total episodes: {len(eps)}")
        if eps:
            first_ep = eps[0]
            print(f"  EP 1 Stream URL: {first_ep.get('stream_url')[:80]}...")
            print(f"  EP 1 Is Online Stream: {first_ep.get('is_online_stream')}")
            assert first_ep.get('stream_url'), "EP 1 must have authentic stream_url"
    
    print("\n✅ Stream Cluster Resolution Passed 100%!")


def test_batch_download_real_video():
    print("\n" + "=" * 60)
    print("2. TESTING ACTUAL BATCH DOWNLOAD WITH FFMPEG (EP 1 & EP 4)")
    print("=" * 60)
    
    test_save_dir = Path("scratch/test_dl")
    test_save_dir.mkdir(parents=True, exist_ok=True)
    
    d = {"id": "hg_test_01", "title": "《东北话事人》", "title_cn": "东北话事人", "platform": "Hongguo"}
    drama_downloader.current_drama = d
    drama_downloader.episodes = get_drama_episodes(d)
    
    print(f"Total resolved episodes in drama: {len(drama_downloader.episodes)}")
    
    # Download EP 1 and EP 4 (EP 4 was the one that previously failed on Hongguo web!)
    res = drama_downloader.start_download_batch(
        episode_ids=["ep_001", "ep_004"],
        save_location=str(test_save_dir),
        save_poster=True
    )
    print("Start download result:", res)
    
    # Poll status until done
    for i in range(120):
        time.sleep(1)
        st = drama_downloader.stats
        is_dl = drama_downloader.is_downloading
        print(f"[{i+1}s] Downloading: {is_dl} | Completed: {st['completed']}/2 | Failed: {st['failed']}")
        if not is_dl and (st['completed'] + st['failed']) >= 2:
            break
            
    print("\nFinal Downloader Logs:")
    for line in drama_downloader.logs[-10:]:
        print("  ", line)
        
    drama_folder = test_save_dir / "东北话事人"
    ep1_file = drama_folder / "EP_01.mp4"
    ep4_file = drama_folder / "EP_04.mp4"
    
    assert ep1_file.exists(), f"EP_01.mp4 must exist at {ep1_file}"
    assert ep4_file.exists(), f"EP_04.mp4 must exist at {ep4_file}"
    
    sz1_mb = ep1_file.stat().st_size / (1024 * 1024)
    sz4_mb = ep4_file.stat().st_size / (1024 * 1024)
    
    print(f"\n📁 EP_01.mp4 Size: {sz1_mb:.2f} MB")
    print(f"📁 EP_04.mp4 Size: {sz4_mb:.2f} MB")
    
    # Both must be authentic full video files (> 5 MB), NOT 30s dummy clips (< 1 MB)!
    assert sz1_mb > 5.0, f"EP_01.mp4 must be authentic full video (> 5 MB), got {sz1_mb} MB"
    assert sz4_mb > 5.0, f"EP_04.mp4 must be authentic full video (> 5 MB), got {sz4_mb} MB"
    
    print("\n🎉 ALL TESTS PASSED! 100% GENUINE DRAMA VIDEOS DOWNLOADED!")

if __name__ == "__main__":
    test_stream_cluster_resolution()
    test_batch_download_real_video()
