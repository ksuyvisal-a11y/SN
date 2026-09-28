import os
import sys
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import logging

logging.basicConfig(level=logging.INFO)
import downloader

def test_download():
    d = downloader.DramaDownloadManager()
    print("Testing analyze_url...")
    res = d.analyze_url("东北话事人")
    print(f"Analyze success: {res.get('success')}, episodes detected: {len(res.get('episodes', []))}")
    if not res.get("episodes"):
        print("No episodes found!")
        return

    # Select only 2 episodes for quick test download
    test_eps = [res["episodes"][0]["id"], res["episodes"][1]["id"]]
    save_dir = "d:/Sal/SN/test_output_dramas"
    print(f"Starting batch download for {test_eps} to {save_dir}...")
    d.start_download_batch(test_eps, save_dir, save_poster=True, auto_merge_full=False)

    # Wait for download thread to finish
    while d.is_downloading:
        time.sleep(2)
        stats = d.stats
        print(f"Progress: {stats.get('progress_percent')}% | Completed: {stats.get('completed')} | Failed: {stats.get('failed')}")

    print("Download finished!")
    print(f"Final stats: {d.stats}")
    for l in d.logs[-15:]:
        print(f"  Log: {l}")

if __name__ == "__main__":
    test_download()
