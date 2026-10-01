import sys
import json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Check how many streams in data/ai_dramas_streams.json have share URLs instead of .m3u8
streams_path = Path("data/ai_dramas_streams.json")
with open(streams_path, "r", encoding="utf-8") as f:
    streams = json.load(f)

share_count = 0
m3u8_count = 0
other_count = 0

for did, dinfo in streams.items():
    purl = dinfo.get("play_url", "")
    if "share/" in purl and ".m3u8" not in purl:
        share_count += 1
    elif ".m3u8" in purl:
        m3u8_count += 1
    else:
        other_count += 1

print(f"Total streams in cache: {len(streams):,}")
print(f"Direct M3U8 streams:     {m3u8_count:,}")
print(f"Share page URLs (BAD):   {share_count:,}")
print(f"Other / MP4 URLs:        {other_count:,}")
