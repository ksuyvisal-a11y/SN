import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout.reconfigure(encoding='utf-8')
from downloader import resolve_hongguo_series_vids, get_hongguo_episode_real_stream_url

sid = "7683196130645003288"
vids = resolve_hongguo_series_vids(sid)
print(f"Total vids found: {len(vids)}")
print(f"First 5 vids: {vids[:5]}")

for idx in range(min(3, len(vids))):
    v = vids[idx]
    stream_url = get_hongguo_episode_real_stream_url(sid, v)
    print(f"EP {idx+1} (vid={v}): stream_url={stream_url[:80]}..." if stream_url else f"EP {idx+1} (vid={v}): NO URL")
