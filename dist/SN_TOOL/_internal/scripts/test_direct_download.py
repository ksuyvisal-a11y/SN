import sys
import os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
app_path = r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app"
sys.path.insert(0, app_path)
os.environ["SIGN_SERVER"] = "http://127.0.0.1:9099"

import offline_dl

test_out = Path(r"D:\SN_Dramas\Test_Download")
test_out.mkdir(parents=True, exist_ok=True)
offline_dl.set_output_dir(str(test_out))
print("offline_dl.OUT is now:", offline_dl.OUT)

sid = "7683196130645003288"
print(f"Starting download for series {sid} (Episodes 1-2)...")

# dl_series(series_id, rng='all', concurrency=4, retry_rounds=2, quality='best')
try:
    res = offline_dl.dl_series(sid, rng="1-2", concurrency=2, quality="1080p")
    print("dl_series returned:", res)
    print("\nFiles in test_out:")
    for f in test_out.rglob("*"):
        if f.is_file():
            print(f" - {f.relative_to(test_out)} ({f.stat().st_size / (1024*1024):.2f} MB)")
except Exception as e:
    import traceback
    traceback.print_exc()
