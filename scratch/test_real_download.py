import sys
import time
import shutil
from pathlib import Path

sys.path.insert(0, ".")
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
import downloader
import hongguo_db

# 1. Fetch Rank 1 drama 《东北话事人》
drama = hongguo_db.get_drama_by_id("hg_7683196130645003288")
print("Drama fetched:", drama["title"], "Episodes:", drama["total_episodes"])

# 2. Analyze URL / drama
res = downloader.drama_downloader.analyze_url("东北话事人")
assert res["success"] is True
print("Episodes count in manifest:", len(downloader.drama_downloader.episodes))

# 3. Test Download with EP 1 & EP 2
test_dir = Path("D:/SN_Dramas_Verify")
if test_dir.exists():
    shutil.rmtree(test_dir, ignore_errors=True)
test_dir.mkdir(parents=True, exist_ok=True)

# Test with short IDs: ['ep_1', 'ep_2'] (as sent by UI)
dl_res = downloader.drama_downloader.start_download_batch(
    episode_ids=['ep_1', 'ep_2'],
    save_location=str(test_dir),
    save_poster=True
)
print("Start download batch result:", dl_res)

# Wait for completion
for i in range(40):
    time.sleep(0.2)
    if not downloader.drama_downloader.is_downloading:
        break

# Verify output folder
subdirs = list(test_dir.glob("*"))
print("Created subdirs:", [d.name for d in subdirs])
assert len(subdirs) > 0, "No drama subfolder created!"

target_folder = subdirs[0]
mp4s = list(target_folder.glob("*.mp4"))
posters = list(target_folder.glob("*Poster.jpg"))
infos = list(target_folder.glob("*Story_Info.txt"))

print(f"\nResults in '{target_folder.name}':")
print(f"  - MP4 files ({len(mp4s)}): {[f.name + ' (' + str(round(f.stat().st_size/(1024*1024), 1)) + ' MB)' for f in mp4s]}")
print(f"  - Posters ({len(posters)}): {[f.name for f in posters]}")
print(f"  - Story Info ({len(infos)}): {[f.name for f in infos]}")

if infos:
    print("\n--- Story Info Snippet ---")
    print(infos[0].read_text(encoding="utf-8")[:400])

assert len(mp4s) == 2, f"Expected 2 MP4 files, got {len(mp4s)}!"
for mp4 in mp4s:
    assert mp4.stat().st_size > 1000000, f"MP4 {mp4.name} is too small ({mp4.stat().st_size} bytes)!"

assert len(posters) >= 1, "Poster missing!"
assert len(infos) >= 1, "Story Info missing!"

# Cleanup test directory
shutil.rmtree(test_dir, ignore_errors=True)
print("\n🎉 REAL DRAMA VIDEO & STORY DOWNLOAD TEST PASSED 100%!")
