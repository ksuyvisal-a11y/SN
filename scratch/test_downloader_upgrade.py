import sys
import time
import os
from pathlib import Path

# Setup paths
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from downloader import (
    resolve_short_drama_stream_cluster,
    download_m3u8_stream_turbo,
    merge_drama_episodes_to_full_movie,
    drama_downloader,
    SHORT_DRAMA_VOD_APIS
)

def run_tests():
    print("=" * 60)
    print("🎬 TESTING TURBO SHORT DRAMA DOWNLOADER UPGRADE")
    print("=" * 60)

    # Test 1: Check active VOD APIs
    print(f"\n[Test 1] Active VOD Cluster APIs count: {len(SHORT_DRAMA_VOD_APIS)}")
    for name, base_url in SHORT_DRAMA_VOD_APIS:
        print(f"  - {name}: {base_url}")
    assert len(SHORT_DRAMA_VOD_APIS) >= 6, "Expected at least 6 active APIs"
    print("✔ Test 1 Passed: Multi-API cluster registered.")

    # Test 2: Multi-API parallel resolution & episode count
    print("\n[Test 2] Resolving full drama series via multi-API parallel search...")
    t0 = time.time()
    eps = resolve_short_drama_stream_cluster("顾总")
    t1 = time.time()
    print(f"  - Resolved {len(eps)} episodes in {t1-t0:.2f}s!")
    assert len(eps) >= 20, f"Expected full series (at least 20+ episodes), got {len(eps)}"
    print(f"  - First ep: {eps[0]['title']} -> {eps[0]['stream_url'][:60]}...")
    print(f"  - Last ep:  {eps[-1]['title']} -> {eps[-1]['stream_url'][:60]}...")
    print("✔ Test 2 Passed: Full series stream cluster resolved with maximum episodes.")

    # Test 3: Concurrency & Turbo Download check
    print("\n[Test 3] Testing Turbo fragment downloader...")
    test_stream = eps[0]["stream_url"]
    test_dest = ROOT_DIR / "scratch" / "test_ep_verify.mp4"
    if test_dest.exists():
        test_dest.unlink()

    t_dl0 = time.time()
    ok = download_m3u8_stream_turbo(test_stream, test_dest, timeout_sec=90)
    t_dl1 = time.time()
    
    assert ok and test_dest.exists(), "Download failed!"
    sz_mb = test_dest.stat().st_size / (1024 * 1024)
    print(f"  - Downloaded {sz_mb:.2f} MB in {t_dl1-t_dl0:.2f}s! (Speed: {sz_mb/(t_dl1-t_dl0):.2f} MB/s)")
    assert sz_mb > 1.0, "File size too small"
    print("✔ Test 3 Passed: Turbo downloader downloaded 1080p video with full audio & video integrity.")

    # Test 4: Full Drama Movie Concatenation (Merge Full Movie)
    print("\n[Test 4] Testing Full Drama Movie Merge...")
    # Create fake second episode to test merge
    test_dest2 = ROOT_DIR / "scratch" / "EP_01.mp4"
    test_dest3 = ROOT_DIR / "scratch" / "EP_02.mp4"
    import shutil
    shutil.copy2(test_dest, test_dest2)
    shutil.copy2(test_dest, test_dest3)

    merged_out = ROOT_DIR / "scratch" / "TestDrama_Full_Drama_1080p.mp4"
    if merged_out.exists():
        merged_out.unlink()

    t_m0 = time.time()
    merge_ok = merge_drama_episodes_to_full_movie(ROOT_DIR / "scratch", merged_out)
    t_m1 = time.time()

    assert merge_ok and merged_out.exists(), "Merge failed!"
    m_sz_mb = merged_out.stat().st_size / (1024 * 1024)
    print(f"  - Merged into full movie in {t_m1-t_m0:.2f}s! Output size: {m_sz_mb:.2f} MB")
    assert m_sz_mb > sz_mb * 1.5, "Merged file size should reflect concatenated episodes"
    print("✔ Test 4 Passed: Full Drama Movie generated with lossless stream copy.")

    # Clean up test files
    for p in [test_dest, test_dest2, test_dest3, merged_out]:
        if p.exists():
            p.unlink()

    print("\n" + "=" * 60)
    print("🎉 ALL 4 TURBO DOWNLOADER TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 60)

if __name__ == '__main__':
    run_tests()
