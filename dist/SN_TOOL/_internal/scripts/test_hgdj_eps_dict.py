import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
app_path = r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app"
sys.path.insert(0, app_path)
os.environ["SIGN_SERVER"] = "http://127.0.0.1:9099"

import offline_dl

sid = "7683196130645003288"
eps = offline_dl.hgdj_episodes(sid)
print("Keys:", eps.keys())
print("series_title:", eps.get("title"))
print("episode_cnt:", eps.get("episode_cnt"))
print("episodes count:", len(eps.get("episodes", [])))
if eps.get("episodes"):
    print("Ep 1:", eps["episodes"][0])
    print("Ep 4:", eps["episodes"][3] if len(eps["episodes"]) > 3 else "N/A")
    print("Last ep:", eps["episodes"][-1])
