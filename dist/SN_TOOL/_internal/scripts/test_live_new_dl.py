import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import downloader
import hongguo_db

sys.stdout.reconfigure(encoding='utf-8')

drama = hongguo_db.get_drama_by_id('reelshort_6a469b12d3f5c65f7f095b8a')
print("Drama retrieved:", drama['title'])

eps = downloader.get_drama_episodes(drama)
print(f"Total episodes: {len(eps)}")
ep1 = eps[0]
print("EP 1 stream:", ep1.get('stream_url'))

save_dir = Path("downloads/test_new_reelshort")
save_dir.mkdir(parents=True, exist_ok=True)
print("Testing live download of Episode 1...")
res = downloader.download_single_ep(ep1, drama, save_dir)
print("Download result:", res)

for f in sorted(save_dir.glob("*")):
    print(f" -> File saved: {f.name} ({f.stat().st_size / 1024 / 1024:.2f} MB)")
