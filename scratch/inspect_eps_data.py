import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path

HG_ROOT = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader")
APP_DIR = HG_ROOT / "app"
sys.path.insert(0, str(APP_DIR))
os.environ["SIGN_SERVER"] = "http://127.0.0.1:9099"

import hongguo

res = hongguo.get_episodes("7683196130645003288")
print(f"Tuple length: {len(res)}")
for i, item in enumerate(res):
    print(f"\nItem {i} ({type(item)}):")
    if isinstance(item, list):
        print(f"  List of {len(item)} elements")
        if item:
            print("  First element:", item[0])
            print("  Second element:", item[min(1, len(item)-1)])
    elif isinstance(item, dict):
        print("  Dict keys:", list(item.keys()))
        for k in list(item.keys())[:5]:
            print(f"    {k}:", str(item[k])[:80])
    else:
        print("  Value:", str(item)[:120])
