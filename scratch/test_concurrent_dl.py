import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import sys
sys.path.insert(0, ".")
import downloader

test_dir = Path("scratch/test_concurrent_dl")
test_dir.mkdir(parents=True, exist_ok=True)

streams = [
    ("EP 1", "https://play.modujx17.com/20260920/n8GveYyN/index.m3u8", test_dir / "EP_01.mp4"),
    ("EP 2", "https://play.modujx17.com/20260920/6tHCXNUr/index.m3u8", test_dir / "EP_02.mp4"),
    ("EP 3", "https://play.modujx17.com/20260920/05AyDGKM/index.m3u8", test_dir / "EP_03.mp4"),
]

def dl_ep(name, url, dest):
    t0 = time.time()
    ok = downloader.download_m3u8_stream_with_ffmpeg(url, dest, timeout_sec=60)
    sz = dest.stat().st_size / (1024*1024) if dest.exists() else 0
    print(f"{name}: {'OK' if ok else 'FAIL'} ({sz:.1f} MB) in {time.time()-t0:.1f}s")
    return ok

print("Starting 3 concurrent episode downloads...")
start_all = time.time()
with ThreadPoolExecutor(max_workers=3) as pool:
    futs = [pool.submit(dl_ep, n, u, d) for n, u, d in streams]
    for f in as_completed(futs):
        pass

total_time = time.time() - start_all
print(f"All 3 episodes downloaded concurrently in {total_time:.2f}s!")
