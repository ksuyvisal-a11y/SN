import sys
import os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
app_path = r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app"
sys.path.insert(0, app_path)
os.environ["SIGN_SERVER"] = "http://127.0.0.1:9099"

import offline_dl

test_out = Path(r"D:\SN_Dramas\Test_Runner")
offline_dl.set_output_dir(str(test_out))

sid = "7686843598813613081" # 我的战友全是大佬 (47 episodes)
print(f"Downloading Episode 1 of series #{sid} into {test_out}...")

res = offline_dl.dl_series(sid, rng="1", concurrency=1, quality="1080p")
print("Download result:", res)
