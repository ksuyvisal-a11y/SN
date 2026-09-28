import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')
sys.path.insert(0, 'data')
import hongguo_db
from downloader import get_drama_episodes, resolve_short_drama_stream_cluster

dramas, total = hongguo_db.query_dramas(limit=10)
print(f"Total: {total}")
for i, d in enumerate(dramas):
    title = d.get('title_cn') or d.get('title')
    eps = get_drama_episodes(d)
    valid_streams = [e for e in eps if e.get('stream_url') and ('http' in str(e.get('stream_url')) or '.m3u8' in str(e.get('stream_url')))]
    print(f"{i+1}. Drama: {title} (ID: {d.get('id')}) -> {len(eps)} total eps, {len(valid_streams)} valid stream URLs")
    if valid_streams:
        print(f"   Stream Sample: {valid_streams[0].get('stream_url')[:80]}")
    elif eps:
        print(f"   Fallback stream_url sample: {eps[0].get('stream_url')}")
