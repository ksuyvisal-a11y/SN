import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent.parent))

from downloader import drama_downloader

drama_id = "hg_7683196130645003288"
print(f"Analyzing {drama_id}...")
analysis = drama_downloader.analyze_url(drama_id)
print("Analysis success:", analysis.get("success"))
print("Drama title:", analysis.get("drama", {}).get("title"))
print("Total episodes:", len(analysis.get("episodes", [])))

# Test downloading Episode 3 and 4 (Episode 4 was previously failing due to ByteDance encryption!)
eps = analysis.get("episodes", [])
ep3_id = eps[2]["id"] if len(eps) > 2 else eps[0]["id"]
ep4_id = eps[3]["id"] if len(eps) > 3 else eps[0]["id"]
selected_ids = [ep3_id, ep4_id]

save_dest = "D:/SN_Dramas/Test_Hongguo_Batch"
print(f"\nStarting batch download for {selected_ids} to {save_dest}...")
res = drama_downloader.start_download_batch(selected_ids, save_location=save_dest, auto_merge_full=False)
print("start_download_batch result:", res)

for i in range(40):
    time.sleep(2)
    stats = drama_downloader.stats
    print(f"[{i*2}s] Completed: {stats.get('completed')}/{stats.get('total')} (Failed: {stats.get('failed')}, {stats.get('progress_percent')}%)")
    if not drama_downloader.is_downloading:
        print("Batch download finished!")
        break

print("\nRecent Downloader Logs:")
for l in drama_downloader.logs[-12:]:
    print(" ", l)

# Check files on disk
p_dest = Path(save_dest)
print(f"\nFiles in {save_dest}:")
for f in p_dest.rglob("*.mp4"):
    print(f" - {f.name} ({f.stat().st_size / (1024*1024):.2f} MB)")
