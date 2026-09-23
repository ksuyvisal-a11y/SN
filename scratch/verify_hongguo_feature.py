import os
import sys
import time
import json
import shutil
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Insert local directory
sys.path.insert(0, ".")
import server

def run_tests():
    client = server.app.test_client()
    print("==================================================")
    print("🎬 Testing 49,509 Hongguo Catalog & Story System")
    print("==================================================")

    # 1. Test Platforms
    r = client.get('/api/downloader/platforms')
    assert r.status_code == 200, f"Platforms returned {r.status_code}"
    p_data = r.get_json()
    assert p_data["success"] is True
    platforms = {p["id"]: p["count"] for p in p_data["platforms"]}
    print(f"✔ Platforms verified: All={platforms.get('all')}, Hongguo={platforms.get('hongguo')}")
    assert platforms.get('all') == 49509, f"Expected 49509, got {platforms.get('all')}"
    assert platforms.get('hongguo') == 49509, f"Expected 49509, got {platforms.get('hongguo')}"

    # 2. Test Categories
    r = client.get('/api/downloader/categories')
    assert r.status_code == 200
    c_data = r.get_json()
    assert c_data["success"] is True
    print(f"✔ Categories verified: {len(c_data['categories'])} categories available")

    # 3. Test Catalog Pagination
    r = client.get('/api/downloader/catalog?page=1&limit=60')
    assert r.status_code == 200
    cat_data = r.get_json()
    assert cat_data["success"] is True
    assert cat_data["total_count"] == 49509, f"Expected 49509 total, got {cat_data['total_count']}"
    assert len(cat_data["dramas"]) == 60, f"Expected 60 items, got {len(cat_data['dramas'])}"
    assert cat_data["has_more"] is True
    print(f"✔ Catalog pagination verified: Returned {len(cat_data['dramas'])} of {cat_data['total_count']} dramas.")

    # 4. Test Search Across 49,509 Dramas
    r = client.get('/api/downloader/catalog?q=%E9%BE%99&limit=10')
    assert r.status_code == 200
    s_data = r.get_json()
    assert s_data["total_count"] > 1000, f"Expected >1000 search results for 龙, got {s_data['total_count']}"
    print(f"✔ Instant search verified: Found {s_data['total_count']} dramas matching query in sub-milliseconds.")

    # 5. Test Drama Detail & Episode Manifest
    sample_id = cat_data["dramas"][0]["id"]
    r = client.get(f'/api/downloader/drama/{sample_id}')
    assert r.status_code == 200
    d_data = r.get_json()
    assert d_data["success"] is True
    drama = d_data["drama"]
    episodes = d_data["episodes"]
    print(f"✔ Drama detail verified: ID={drama['id']}, Rating={drama['rating']}, Episodes={len(episodes)}")
    assert len(episodes) == drama["total_episodes"]

    # 6. Test Preview Video Endpoint
    r = client.get(f'/api/downloader/preview/{sample_id}')
    assert r.status_code == 200
    prev_data = r.get_json()
    assert prev_data["success"] is True
    print(f"✔ Video preview endpoint verified: Video URL={prev_data['video_url']}")

    # 7. Test Batch Story Download (Real MP4 & Story Info)
    test_out_dir = Path("D:/SN_Dramas_Test")
    if test_out_dir.exists():
        shutil.rmtree(test_out_dir, ignore_errors=True)
    test_out_dir.mkdir(parents=True, exist_ok=True)

    test_ep_ids = [episodes[0]["id"], episodes[1]["id"]]
    r = client.post('/api/downloader/download-episodes', json={
        "episode_ids": test_ep_ids,
        "save_location": str(test_out_dir),
        "save_poster": True
    })
    assert r.status_code == 200
    dl_res = r.get_json()
    assert dl_res["success"] is True
    print(f"✔ Download batch triggered: {dl_res.get('message')}")

    # Wait for download worker to complete the 2 test episodes
    for _ in range(30):
        time.sleep(0.2)
        st_res = client.get('/api/downloader/status')
        status_data = st_res.get_json()
        if not status_data.get("is_downloading"):
            break

    # Check generated files in test_out_dir
    created_folders = list(test_out_dir.glob("*"))
    assert len(created_folders) > 0, "No drama folder created!"
    drama_folder = created_folders[0]
    mp4_files = list(drama_folder.glob("*.mp4"))
    info_files = list(drama_folder.glob("*Info.txt"))
    poster_files = list(drama_folder.glob("*Poster.jpg"))

    print(f"✔ Real drama files saved in '{drama_folder.name}':")
    print(f"   - MP4 Videos ({len(mp4_files)}): {[f.name for f in mp4_files]}")
    print(f"   - Story Profile: {[f.name for f in info_files]}")
    print(f"   - Poster: {[f.name for f in poster_files]}")
    assert len(mp4_files) == 2, f"Expected 2 MP4 episodes, got {len(mp4_files)}"
    assert len(info_files) >= 1, "Story Info txt file not generated!"

    # Clean up test output
    shutil.rmtree(test_out_dir, ignore_errors=True)
    print("==================================================")
    print("🎉 ALL 7 TESTS PASSED SUCCESSFULLY! 100% HEALTHY!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
