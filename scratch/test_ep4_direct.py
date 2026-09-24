import os
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from downloader import drama_downloader, get_drama_episodes

test_save_dir = Path("scratch/test_dl")
d = {"id": "hg_test_01", "title": "《东北话事人》", "title_cn": "东北话事人", "platform": "Hongguo"}
drama_downloader.current_drama = d
drama_downloader.episodes = get_drama_episodes(d)

print(f"Starting single download for EP 4...")
drama_downloader.start_download_batch(
    episode_ids=["ep_004"],
    save_location=str(test_save_dir),
    save_poster=False
)

while drama_downloader.is_downloading:
    time.sleep(2)
    st = drama_downloader.stats
    print(f"Status: Completed {st['completed']}/1 | Failed {st['failed']}")

print("\nLogs:")
for l in drama_downloader.logs[-6:]:
    print("  ", l)

ep4_file = test_save_dir / "东北话事人" / "EP_04.mp4"
if ep4_file.exists():
    sz_mb = ep4_file.stat().st_size / (1024 * 1024)
    print(f"\n🎉 EP_04.mp4 exists! Size: {sz_mb:.2f} MB")
    assert sz_mb > 5.0, f"EP_04.mp4 size must be > 5MB, got {sz_mb} MB"
    print("✅ EP 4 TEST PASSED 100%!")
else:
    print("❌ EP_04.mp4 was not downloaded.")
    sys.exit(1)
