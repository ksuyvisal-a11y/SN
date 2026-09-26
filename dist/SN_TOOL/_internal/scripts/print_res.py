import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
app_path = r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app"
sys.path.insert(0, app_path)
os.environ["SIGN_SERVER"] = "http://127.0.0.1:9099"

import offline_dl
sid = "7683196130645003288"
res = offline_dl.hgdj_episodes([sid])
print("res:", res)
