import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from pathlib import Path
import downloader

def test_slicing():
    test_src = Path("d:/Sal/SN/test_output_dramas/东北话事人/EP_01.mp4")
    out_dir = Path("d:/Sal/SN/test_output_dramas/test_slice_dir")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Testing slicing {test_src} into 3 parts...")
    res = downloader.slice_full_movie_into_episodes(test_src, out_dir, total_episodes=3)
    print(f"Slice result: {res}")
    files = list(out_dir.glob("*.mp4"))
    print(f"Files created in {out_dir}: {len(files)}")
    for f in sorted(files):
        print(f"  {f.name}: {f.stat().st_size} bytes")

if __name__ == "__main__":
    test_slicing()
