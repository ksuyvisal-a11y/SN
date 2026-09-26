import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
app_path = r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app"
sys.path.insert(0, app_path)
os.environ["SIGN_SERVER"] = "http://127.0.0.1:9099"

import offline_dl
import inspect

print("hgdj_episodes signature:", inspect.signature(offline_dl.hgdj_episodes))
sid = "7683196130645003288"
res = offline_dl.hgdj_episodes([sid])
print("res type:", type(res))
if isinstance(res, dict):
    print("res keys:", list(res.keys()))
    val = res.get(sid)
    print("val for sid:", type(val), len(val) if val else 0)
    if val and isinstance(val, list):
        print("First 2 episodes in val:")
        for ep in val[:2]:
            print(ep)
        print("Last episode in val:", val[-1])
