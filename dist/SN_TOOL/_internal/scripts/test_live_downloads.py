import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import downloader
import hongguo_db

print("=" * 60)
print("🧪 LIVE DOWNLOAD TEST ACROSS ALL 3 PLATFORMS")
print("=" * 60)

test_dir = Path("D:/SN_Dramas/TEST_DOWNLOAD") if Path("D:/").exists() else Path("C:/SN_Dramas/TEST_DOWNLOAD")
test_dir.mkdir(parents=True, exist_ok=True)

# 1. Test AI drama download
print("\n[1/3] Testing AI Drama download...")
ai_drama = hongguo_db.get_drama_by_id("ai_164689")
if ai_drama:
    eps = downloader.get_drama_episodes(ai_drama)
    print(f"  AI Drama: {ai_drama['title']}, Eps: {len(eps)}")
    if eps and eps[0].get("stream_url"):
        stream_u = eps[0]["stream_url"]
        out_f = test_dir / "AI_Test_EP01.mp4"
        print(f"  Downloading from: {stream_u[:60]}...")
        ok = downloader.download_m3u8_stream_turbo(stream_u, out_f, timeout_sec=60)
        print(f"  Result: {'✅ SUCCESS' if ok and out_f.exists() else '❌ FAILED'}")
        if out_f.exists():
            print(f"  File size: {out_f.stat().st_size / (1024*1024):.2f} MB")
            out_f.unlink()

# 2. Test ShortMax download
print("\n[2/3] Testing ShortMax download...")
sm_drama = hongguo_db.get_drama_by_id("shortmax_44413")
if sm_drama:
    eps = downloader.get_drama_episodes(sm_drama)
    print(f"  ShortMax Drama: {sm_drama['title'][:30]}, Eps: {len(eps)}")
    if eps and eps[0].get("stream_url"):
        stream_u = eps[0]["stream_url"]
        out_f = test_dir / "SM_Test_EP01.mp4"
        print(f"  Downloading from: {stream_u[:60]}...")
        ok = downloader.download_m3u8_stream_turbo(stream_u, out_f, timeout_sec=60)
        print(f"  Result: {'✅ SUCCESS' if ok and out_f.exists() else '❌ FAILED'}")
        if out_f.exists():
            print(f"  File size: {out_f.stat().st_size / (1024*1024):.2f} MB")
            out_f.unlink()

# 3. Test Hongguo drama download
print("\n[3/3] Testing Hongguo Leaderboard Drama download...")
hg_drama = hongguo_db.get_drama_by_id("hg_7683196130645003288") # 东北话事人
if hg_drama:
    print(f"  Resolving streams for: {hg_drama.get('title_cn')}...")
    cluster_eps = downloader.resolve_short_drama_stream_cluster(hg_drama.get('title_cn'))
    print(f"  Found {len(cluster_eps)} cluster episodes.")
    if cluster_eps and cluster_eps[0].get("stream_url"):
        stream_u = cluster_eps[0]["stream_url"]
        out_f = test_dir / "HG_Test_EP01.mp4"
        print(f"  Downloading from: {stream_u[:60]}...")
        ok = downloader.download_m3u8_stream_turbo(stream_u, out_f, timeout_sec=60)
        print(f"  Result: {'✅ SUCCESS' if ok and out_f.exists() else '❌ FAILED'}")
        if out_f.exists():
            print(f"  File size: {out_f.stat().st_size / (1024*1024):.2f} MB")
            out_f.unlink()
