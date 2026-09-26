import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent.parent))

from downloader import drama_downloader
import hongguo_db

# Query dramas
dramas, count = hongguo_db.query_dramas(limit=5)
print(f"Total dramas in DB: {count}")
for d in dramas:
    print(f" - [{d['id']}] {d['title']} (Episodes: {d.get('total_episodes')})")

# Let's test analyzing the first drama:
test_drama = dramas[0]
print(f"\nAnalyzing: {test_drama['title']} (ID: {test_drama['id']})...")
analysis = drama_downloader.analyze_url(test_drama['id'])
print("Analysis success:", analysis.get("success"))
print("Total episodes:", len(analysis.get("episodes", [])))
if analysis.get("episodes"):
    print("Ep 1:", analysis["episodes"][0]["title"], "stream_url:", analysis["episodes"][0].get("stream_url"))
    print("Ep 4:", analysis["episodes"][3]["title"] if len(analysis["episodes"]) > 3 else "N/A")

# Let's test downloading Episode 1-2
selected_ids = [analysis["episodes"][0]["id"], analysis["episodes"][1]["id"]]
save_dest = "D:/SN_Dramas/Test_Studio_Batch"
print(f"\nStarting batch download for {selected_ids} to {save_dest}...")
res = drama_downloader.start_download_batch(selected_ids, save_location=save_dest, auto_merge_full=False)
print("start_download_batch returned:", res)

# Monitor progress for up to 60 seconds
for _ in range(30):
    time.sleep(2)
    stats = drama_downloader.stats
    print(f"Progress: {stats.get('completed')}/{stats.get('total')} (Failed: {stats.get('failed')}, {stats.get('progress_percent')}%)")
    if not drama_downloader.is_downloading:
        print("Download queue finished!")
        break

print("\nRecent Downloader Logs:")
for l in drama_downloader.logs[-10:]:
    print(" ", l)
