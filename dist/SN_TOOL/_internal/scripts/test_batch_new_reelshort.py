import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from downloader import drama_downloader, get_drama_episodes
import hongguo_db

drama_id = 'reelshort_6a469b12d3f5c65f7f095b8a'
drama = hongguo_db.get_drama_by_id(drama_id)
print(f"Testing drama: {drama['title']} ({drama['platform']})")

episodes = get_drama_episodes(drama)
print(f"Generated {len(episodes)} episodes.")

drama_downloader.current_drama = drama
drama_downloader.episodes = episodes
drama_downloader.stats["total"] = len(episodes)
drama_downloader.stats["selected"] = 1
drama_downloader.stats["completed"] = 0
drama_downloader.stats["failed"] = 0

ep1 = episodes[0]
save_dir = "downloads/test_batch_reelshort"

print(f"Starting batch download for Episode 1 ({ep1['id']})...")
res = drama_downloader.start_download_batch([ep1['id']], save_dir, save_poster=True)
print("Batch start response:", res)

# Monitor download progress until completed or 30s timeout
start_time = time.time()
while time.time() - start_time < 30:
    stats = drama_downloader.get_stats()
    print(f"[{int(time.time() - start_time)}s] Stats: completed={stats['completed']}, failed={stats['failed']}, is_downloading={drama_downloader.is_downloading}")
    if not drama_downloader.is_downloading and stats['completed'] > 0:
        break
    time.sleep(2)

print("\n--- Recent Downloader Logs ---")
for log in drama_downloader.get_logs()[-6:]:
    print(" ", log)

# Check files on disk
save_path = Path(save_dir) / drama['title'].replace(':', '_').replace('/', '_')
print(f"\nChecking directory: {save_path}")
if save_path.exists():
    for f in save_path.glob("*"):
        print(f"  -> {f.name} ({f.stat().st_size / 1024 / 1024:.2f} MB)")
