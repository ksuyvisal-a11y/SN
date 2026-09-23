import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from downloader import get_hongguo_episode_real_stream_url, download_video_stream_with_curl

sid = "7683196130645003288"
vid = "7683198247380192281"
url = get_hongguo_episode_real_stream_url(sid, vid)
print("Got URL:", url[:80])

dest = Path("D:/SN_Dramas/东北话事人/EP_01_test.mp4")
if dest.exists():
    dest.unlink()

res = download_video_stream_with_curl(url, dest, timeout_sec=90)
print("Result:", res)
print("File exists?", dest.exists())
if dest.exists():
    print("Size:", dest.stat().st_size)
