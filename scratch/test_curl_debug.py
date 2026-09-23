import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from downloader import get_hongguo_episode_real_stream_url, download_video_stream_with_curl, get_silent_kwargs
import subprocess

sid = "7683196130645003288"
vid = "7683198247380192281"
stream_url = get_hongguo_episode_real_stream_url(sid, vid)
print("Stream URL:", stream_url[:100], "...")

dest_file = Path("scratch/test_curl_debug.mp4")
if dest_file.exists():
    dest_file.unlink()

cmd = [
    "curl.exe",
    "-k", "-L",
    "-H", "Referer: https://hongguoduanju.com/",
    "-H", "Origin: https://hongguoduanju.com",
    "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    stream_url,
    "-o", str(dest_file),
    "--connect-timeout", "10",
    "--max-time", "60",
    "-v"
]
print("Running command...")
r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
print("Returncode:", r.returncode)
print("Stderr head:", r.stderr.decode('utf-8', errors='ignore')[:1000])
print("Dest file exists?", dest_file.exists())
if dest_file.exists():
    print("Dest file size:", dest_file.stat().st_size)
