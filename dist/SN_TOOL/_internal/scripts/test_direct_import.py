import sys
import os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

app_path = r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app"
sys.path.insert(0, app_path)

os.environ["SIGN_SERVER"] = "http://127.0.0.1:9099"

import hongguo
import offline_dl
import licensing

print("Hongguo module:", hongguo)
print("Offline DL module:", offline_dl)
print("Licensing module:", licensing)

H = hongguo.Hongguo()
print("Hongguo instance:", H)
print("H methods:", [m for m in dir(H) if not m.startswith("_")])
