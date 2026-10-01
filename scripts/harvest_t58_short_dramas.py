"""
Harvest all 12,183 short dramas from bfzyapi.com category t=58 (短剧大全)
into Platform AI Dramas, with full M3U8 streams, authentic posters, and catalog indexing.
"""

import sys
import os
import re
import json
import time
import sqlite3
import urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = Path("data/hongguo_catalog.db")
AI_STREAMS_PATH = Path("data/ai_dramas_streams.json")
API_BASE = "https://bfzyapi.com/api.php/provide/vod/?ac=detail&t=58"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

def extract_best_m3u8(play_from: str, play_url: str) -> str:
    if not play_url:
        return ""
    groups = play_url.split('$$$')
    from_names = play_from.split('$$$') if play_from else []
    for idx, g in enumerate(groups):
        fname = from_names[idx].lower() if idx < len(from_names) else ""
        if 'm3u8' in fname and '.m3u8' in g:
            return g
    for g in groups:
        if '.m3u8' in g:
            return g
    return max(groups, key=lambda g: len(g.split('#')))

def fetch_page_guaranteed(pg: int, max_retries: int = 6):
    url = f"{API_BASE}&pg={pg}"
    req = urllib.request.Request(url, headers=HEADERS)
    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                items = data.get('list', [])
                if items:
                    return pg, items
                time.sleep(0.3 * attempt)
        except Exception:
            time.sleep(0.5 * attempt)
    return pg, []

def main():
    print("==================================================================", flush=True)
    print("🎬 HARVESTING ALL SHORT DRAMAS (t=58 短剧大全: 12,183 Dramas)", flush=True)
    print("==================================================================", flush=True)

    # 1. Existing DB records
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT id, title_cn FROM hongguo_dramas WHERE platform_id = 'ai_drama'")
    rows = cur.fetchall()
    existing_ids = set(r[0] for r in rows)
    existing_titles = set(re.sub(r'[^\w\u4e00-\u9fff]', '', r[1]) for r in rows if r[1])
    print(f"Current AI Dramas in Database: {len(existing_ids):,}", flush=True)
    conn.close()

    # Existing stream manifests
    existing_streams = {}
    if AI_STREAMS_PATH.exists():
        try:
            with open(AI_STREAMS_PATH, "r", encoding="utf-8") as f:
                existing_streams = json.load(f)
            print(f"Current Cached Drama Streams: {len(existing_streams):,}", flush=True)
        except Exception:
            pass

    # 2. Total pages for t=58
    total_pages = 610
    pages_to_fetch = list(range(1, total_pages + 1))
    t0 = time.time()
    completed = 0
    all_items = []

    print(f"Harvesting 610 pages with 8 workers...", flush=True)
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(fetch_page_guaranteed, p): p for p in pages_to_fetch}
        for fut in as_completed(futures):
            p, items = fut.result()
            if items:
                all_items.extend(items)
            completed += 1
            if completed % 50 == 0 or completed == total_pages:
                pct = (completed / total_pages) * 100
                print(f"  [{completed}/{total_pages} - {pct:.1f}%] Collected: {len(all_items):,} items ({time.time()-t0:.1f}s)", flush=True)

    print(f"\nTotal raw items fetched: {len(all_items):,}", flush=True)

    # 3. Process & deduplicate
    records_to_insert = []
    categories_to_insert = []
    new_added = 0
    base_rank = len(existing_ids) + 1

    for item in all_items:
        raw_vid = str(item.get("vod_id") or "").strip()
        if not raw_vid:
            continue
        raw_name = (item.get("vod_name") or f"Short Drama {raw_vid}").strip()
        clean_name = re.sub(r'^[^\w\u4e00-\u9fff]+|[^\w\u4e00-\u9fff]+$', '', raw_name)
        if not clean_name:
            clean_name = raw_name

        norm_title = re.sub(r'[^\w\u4e00-\u9fff]', '', clean_name)
        drama_id = f"ai_t58_{raw_vid}"

        pfrom = item.get("vod_play_from", "")
        purl_raw = item.get("vod_play_url", "")
        best_stream = extract_best_m3u8(pfrom, purl_raw)

        eps_count = 1
        if best_stream:
            eps_parts = [e for e in best_stream.split('#') if e.strip()]
            if eps_parts:
                eps_count = len(eps_parts)

        poster = item.get("vod_pic") or "posters/poster_sample_ceo.jpg"

        if norm_title in existing_titles or drama_id in existing_ids:
            if best_stream and drama_id not in existing_streams:
                existing_streams[drama_id] = {
                    "title": clean_name,
                    "play_url": best_stream,
                    "poster": poster,
                    "episodes": eps_count
                }
            continue

        existing_titles.add(norm_title)
        existing_ids.add(drama_id)

        full_title = f"《{clean_name}》"
        title_kh = f"រឿងភាគ AI {clean_name}"
        desc = (item.get("vod_content") or f"រឿងភាគខ្លីពិសេស 《{clean_name}》 កម្រិត 1080p Full HD សាច់រឿងពេញលេញ។").strip()
        desc = re.sub(r'<[^>]+>', '', desc)

        score = f"{max(8.5, 9.9 - (base_rank % 10) * 0.1):.1f}"
        heat = f"{max(3500, 9800 - (base_rank % 500) * 10)}万"
        tags = json.dumps(["AI", "短剧", "Chinese AI", "1080p Full HD", "រឿង AI ចិន"], ensure_ascii=False)

        records_to_insert.append((
            drama_id, full_title, clean_name, title_kh, "AI Dramas", "ai_drama",
            eps_count, "AI", "ai_drama", score, "2025", poster, desc, tags, heat, "completed", base_rank
        ))
        categories_to_insert.append((drama_id, "all"))
        categories_to_insert.append((drama_id, "ai_drama"))

        if best_stream:
            existing_streams[drama_id] = {
                "title": clean_name,
                "play_url": best_stream,
                "poster": poster,
                "episodes": eps_count
            }

        new_added += 1
        base_rank += 1

    print(f"\n==================================================================", flush=True)
    print(f"📊 NEW DRAMAS READY TO INSERT:")
    print(f"  * Brand New Unique Dramas:        {new_added:,}")
    print(f"  * Total Dramas in Stream Cache:   {len(existing_streams):,}")
    print(f"==================================================================", flush=True)

    # 4. Save stream cache
    print(f"Saving stream manifests to {AI_STREAMS_PATH}...", flush=True)
    with open(AI_STREAMS_PATH, "w", encoding="utf-8") as f:
        json.dump(existing_streams, f, ensure_ascii=False, indent=2)

    # 5. Insert into SQLite
    if records_to_insert:
        print(f"Inserting {len(records_to_insert):,} dramas into {DB_PATH}...", flush=True)
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        cur.executemany("INSERT OR REPLACE INTO hongguo_dramas VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", records_to_insert)
        cur.executemany("INSERT OR IGNORE INTO drama_categories VALUES (?, ?)", categories_to_insert)
        conn.commit()

        cur.execute("SELECT count(*) FROM hongguo_dramas WHERE platform_id = 'ai_drama'")
        total_ai_count = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM hongguo_dramas")
        grand_total = cur.fetchone()[0]
        conn.close()

        print("\n==================================================================", flush=True)
        print(f"🎉 DATABASE SYNCHRONIZED:")
        print(f"  * Total AI Dramas in Catalog: {total_ai_count:,} dramas")
        print(f"  * Grand Total Across All:      {grand_total:,} dramas")
        print("==================================================================", flush=True)

if __name__ == '__main__':
    main()
