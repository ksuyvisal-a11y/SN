"""
Expanded AI Dramas Harvester
Collects 100% of all AI Short Dramas from the entire Super VOD Cluster:
- Lzizy (cj.lziapi.com) t=52 (AI漫剧 - 12,159 dramas)
- Modu (moduzy.com) t=42 (AI漫剧 - 1,869 dramas)
- Guangsu (guangsuapi.com) t=52 (AI漫剧 - 391 dramas)
- Baofen (bfzyapi.com) t=74 (AI漫剧 - 12,660 dramas, already ingested)

Merges all into data/hongguo_catalog.db and data/ai_dramas_streams.json
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

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

def extract_best_m3u8_stream(play_from: str, play_url: str) -> str:
    if not play_url:
        return ""
    groups = play_url.split('$$$')
    from_names = play_from.split('$$$') if play_from else []
    
    # 1. Prefer group whose from_name contains 'm3u8'
    for idx, g in enumerate(groups):
        fname = from_names[idx].lower() if idx < len(from_names) else ""
        if 'm3u8' in fname and '.m3u8' in g:
            return g
            
    # 2. Prefer any group containing .m3u8
    for g in groups:
        if '.m3u8' in g:
            return g
            
    # 3. Fallback to longest group
    return max(groups, key=lambda g: len(g.split('#')))

def fetch_provider_page(base_url: str, pg: int, max_retries: int = 5):
    url = f"{base_url}&pg={pg}"
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

def harvest_source(name: str, base_url: str, total_pages: int, prefix: str, max_workers: int = 8):
    print(f"\n🚀 Harvesting {name} ({total_pages} pages)...", flush=True)
    t0 = time.time()
    results = []
    completed = 0
    pages = list(range(1, total_pages + 1))
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_provider_page, base_url, p): p for p in pages}
        for fut in as_completed(futures):
            p, items = fut.result()
            if items:
                results.extend(items)
            completed += 1
            if completed % 50 == 0 or completed == total_pages:
                pct = (completed / total_pages) * 100
                print(f"  [{completed}/{total_pages} - {pct:.1f}%] {name} items collected: {len(results):,} ({time.time()-t0:.1f}s)", flush=True)
                
    print(f"✅ {name} Completed: {len(results):,} total items collected in {time.time()-t0:.1f}s", flush=True)
    return results, prefix

def main():
    print("==================================================================", flush=True)
    print("🤖 EXPANDED GLOBAL AI DRAMAS HARVESTER (Target: 25,000+ Dramas)", flush=True)
    print("==================================================================", flush=True)

    # 1. Load existing database dramas to avoid duplicates
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT id, title_cn FROM hongguo_dramas WHERE platform_id = 'ai_drama'")
    existing_rows = cur.fetchall()
    existing_ids = set(r[0] for r in existing_rows)
    existing_titles = set(re.sub(r'[^\w\u4e00-\u9fff]', '', r[1]) for r in existing_rows if r[1])
    print(f"Current AI Dramas in Database: {len(existing_ids):,}", flush=True)
    conn.close()

    # Load existing streams
    existing_streams = {}
    if AI_STREAMS_PATH.exists():
        try:
            with open(AI_STREAMS_PATH, "r", encoding="utf-8") as f:
                existing_streams = json.load(f)
            print(f"Current Cached Drama Streams: {len(existing_streams):,}", flush=True)
        except Exception:
            pass

    # 2. Define providers to harvest
    providers = [
        ("Lzizy AI (t=52)", "https://cj.lziapi.com/api.php/provide/vod/?ac=detail&t=52", 608, "ai_lz"),
        ("Modu AI (t=42)", "https://www.moduzy.com/api.php/provide/vod/?ac=detail&t=42", 94, "ai_md"),
        ("Guangsu AI (t=52)", "https://api.guangsuapi.com/api.php/provide/vod/?ac=detail&t=52", 20, "ai_gs")
    ]

    all_new_items = []
    for pname, purl, pcount, pprefix in providers:
        items, pfx = harvest_source(pname, purl, pcount, pprefix)
        for it in items:
            all_new_items.append((it, pfx))

    print(f"\nTotal raw items fetched across providers: {len(all_new_items):,}", flush=True)

    # 3. Process items, deduplicate by clean title
    records_to_insert = []
    categories_to_insert = []
    added_count = 0
    updated_streams = 0

    base_rank = len(existing_ids) + 1

    for item, pfx in all_new_items:
        raw_vid = str(item.get("vod_id") or "").strip()
        if not raw_vid:
            continue
            
        raw_name = (item.get("vod_name") or f"AI Drama {raw_vid}").strip()
        clean_name = re.sub(r'^[^\w\u4e00-\u9fff]+|[^\w\u4e00-\u9fff]+$', '', raw_name)
        if not clean_name:
            clean_name = raw_name
            
        norm_title = re.sub(r'[^\w\u4e00-\u9fff]', '', clean_name)
        drama_id = f"{pfx}_{raw_vid}"
        
        pfrom = item.get("vod_play_from", "")
        purl_raw = item.get("vod_play_url", "")
        best_stream = extract_best_m3u8_stream(pfrom, purl_raw)

        # Count episodes
        eps_count = 1
        if best_stream:
            eps_parts = [e for e in best_stream.split('#') if e.strip()]
            if eps_parts:
                eps_count = len(eps_parts)

        poster = item.get("vod_pic") or "posters/poster_sample_ceo.jpg"

        # If already exists by title or ID, ensure stream is cached
        if norm_title in existing_titles or drama_id in existing_ids:
            if best_stream and drama_id not in existing_streams:
                existing_streams[drama_id] = {
                    "title": clean_name,
                    "play_url": best_stream,
                    "poster": poster,
                    "episodes": eps_count
                }
                updated_streams += 1
            continue

        existing_titles.add(norm_title)
        existing_ids.add(drama_id)

        full_title = f"《{clean_name}》"
        title_kh = f"រឿងភាគ AI {clean_name}"
        desc = (item.get("vod_content") or f"រឿងភាគ AI ចិនពិសេស 《{clean_name}》 កម្រិត 1080p Full HD សាច់រឿងពេញលេញ។").strip()
        desc = re.sub(r'<[^>]+>', '', desc) # strip HTML

        score = f"{max(8.5, 9.9 - (base_rank % 10) * 0.1):.1f}"
        heat = f"{max(3500, 9800 - (base_rank % 500) * 10)}万"
        tags = json.dumps(["AI", "AI漫剧", "Chinese AI", "1080p Full HD", "រឿង AI ចិន"], ensure_ascii=False)

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

        added_count += 1
        base_rank += 1

    print(f"\n==================================================================", flush=True)
    print(f"📊 SUMMARY OF NEW ADDITIONS:")
    print(f"  * Brand New Unique AI Dramas Added: {added_count:,}")
    print(f"  * Existing Streams Updated:        {updated_streams:,}")
    print(f"  * Total AI Dramas in Stream Cache:  {len(existing_streams):,}")
    print(f"==================================================================", flush=True)

    # 4. Save stream cache
    print(f"Writing updated stream manifests to {AI_STREAMS_PATH}...", flush=True)
    with open(AI_STREAMS_PATH, "w", encoding="utf-8") as f:
        json.dump(existing_streams, f, ensure_ascii=False, indent=2)

    # 5. Insert into SQLite
    if records_to_insert:
        print(f"Inserting {len(records_to_insert):,} new AI dramas into {DB_PATH}...", flush=True)
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
    else:
        print("No new dramas to insert.")

if __name__ == '__main__':
    main()
