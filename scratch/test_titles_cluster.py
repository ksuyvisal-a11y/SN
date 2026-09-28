import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')
sys.path.insert(0, 'data')
import hongguo_db
from downloader import resolve_short_drama_stream_cluster, get_search_queries_for_title

dramas, _ = hongguo_db.query_dramas(limit=10)
for idx, d in enumerate(dramas):
    title_cn = d.get('title_cn')
    queries = get_search_queries_for_title(title_cn)
    streams = resolve_short_drama_stream_cluster(title_cn)
    print(f"[{idx+1}] {title_cn}")
    print(f"    Queries: {queries}")
    print(f"    Streams found: {len(streams)}")
