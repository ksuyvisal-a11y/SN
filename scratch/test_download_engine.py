import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import logging

logging.basicConfig(level=logging.INFO)

import downloader

def test_vod_resolution():
    print("=== TEST 1: Resolving VOD Drama ===")
    drama = {"title": "东北话事人", "series_id": "test_series_1", "episode_count": 80}
    episodes = downloader.get_drama_episodes(drama)
    print(f"Total episodes resolved: {len(episodes)}")
    urls = [ep.get("download_url") or ep.get("stream_url") for ep in episodes if ep.get("download_url") or ep.get("stream_url")]
    print(f"Episodes with playable URLs: {len(urls)} / {len(episodes)}")
    if urls:
        print(f"Sample URL 1: {urls[0][:80]}...")
        print(f"Sample URL 10: {urls[min(9, len(urls)-1)][:80]}...")

def test_full_series_fallback():
    print("\n=== TEST 2: Master Full Drama Search & Slice ===")
    drama = {"title": "全家把我当乡下老太，都吓傻了", "series_id": "7488349286438964243", "episode_count": 80}
    episodes = downloader.get_drama_episodes(drama)
    print(f"Total episodes resolved: {len(episodes)}")
    urls = [ep.get("download_url") or ep.get("stream_url") for ep in episodes if ep.get("download_url") or ep.get("stream_url")]
    print(f"Episodes with playable URLs: {len(urls)} / {len(episodes)}")
    master_info = downloader._DRAMA_MASTER_STREAM_CACHE.get("7488349286438964243")
    print(f"Master full drama stream found: {master_info is not None}")
    if master_info:
        print(f"Master URL: {master_info.get('url')[:80]}...")

if __name__ == "__main__":
    test_vod_resolution()
    test_full_series_fallback()
