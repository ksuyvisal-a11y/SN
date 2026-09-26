import os
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, ".")
import downloader
import hongguo_db

print("Testing Hongguo database queries and stream resolution...")

# Test 1: 糯糯下山，师兄们都慌了第三季
t1 = '糯糯下山，师兄们都慌了第三季'
r1 = downloader.resolve_short_drama_stream_cluster(t1)
print(f"[{t1}] -> Found {len(r1)} episodes in VOD cluster")
if r1:
    print(f"  EP1 stream: {r1[0].get('stream_url')}")

# Test 2: 东北话事人
t2 = '东北话事人'
r2 = downloader.resolve_short_drama_stream_cluster(t2)
print(f"[{t2}] -> Found {len(r2)} episodes in VOD cluster")
if r2:
    print(f"  EP1 stream: {r2[0].get('stream_url')}")

# Test 3: Check some top dramas from DB
dramas, cnt = hongguo_db.query_dramas(limit=10)
print(f"Total dramas in DB: {cnt}")
for d in dramas[:5]:
    did = d['id']
    dtit = d['title_cn']
    sid = str(d.get('series_id') or did).replace('hg_', '')
    print(f"\nDrama: {dtit} (ID: {did}, SID: {sid})")
    
    # Check VOD cluster
    r = downloader.resolve_short_drama_stream_cluster(dtit)
    print(f"  VOD cluster results: {len(r)}")
    
    # Check ByteDance CDN resolve_hongguo_series_vids
    vids = downloader.resolve_hongguo_series_vids(sid)
    print(f"  Hongguo series VIDs: {len(vids)}")
    if vids:
        surl = downloader.get_hongguo_episode_real_stream_url(sid, vids[0])
        print(f"  EP1 ByteDance stream URL: {surl}")
