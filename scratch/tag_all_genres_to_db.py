"""
Genre Mapper & Indexer for Hongguo Drama Catalog.
Downloads official genre series IDs from https://explorer.hongguodownloader.com/
and maps all 49,509 dramas into their respective categories:
Revenge (16,813), CEO (4,072), War God (4,652), Rebirth (3,604),
Romance (4,856), Doctor (22,425), Palace (8,969), Action (14,016),
AI (13,460), Animated (15,790).
"""
import sys
import os
import time
import json
import sqlite3
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

DB_PATH = Path("data/hongguo_catalog.db")
EXPLORER_API_BASE = "https://explorer.hongguodownloader.com"

GENRE_MAP = [
    {"id": "urban_revenge", "name": "Revenge", "name_kh": "រឿងសងសឹក", "genre": "逆袭"},
    {"id": "billionaire_ceo", "name": "CEO", "name_kh": "រឿងចៅហ្វាយនាយ", "genre": "总裁"},
    {"id": "god_of_war", "name": "War God", "name_kh": "រឿងទេពចម្បាំង", "genre": "大男主"},
    {"id": "rebirth_travel", "name": "Rebirth", "name_kh": "រឿងកើតឡើងវិញ", "genre": "重生"},
    {"id": "sweet_romance", "name": "Romance", "name_kh": "រឿងស្នេហា", "genre": "恋爱"},
    {"id": "divine_doctor", "name": "Doctor", "name_kh": "រឿងគ្រូពេទ្យទេវតា", "genre": "都市"},
    {"id": "palace_historical", "name": "Palace", "name_kh": "រឿងរាជវាំងបុរាណ", "genre": "古代"},
    {"id": "action_suspense", "name": "Action", "name_kh": "រឿងសកម្មភាព", "genre": "剧情"},
    {"id": "ai_drama", "name": "AI", "name_kh": "រឿង AI កំពូល", "genre": "AI"},
    {"id": "animated_drama", "name": "Animated", "name_kh": "រឿងគំនូរជីវចល", "genre": "Animated"}
]

def fetch_genre_page(genre: str, page: int):
    url = f"{EXPLORER_API_BASE}/explorer?page={page}&size=100&genre={urllib.parse.quote(genre)}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=8) as res:
            data = json.loads(res.read().decode("utf-8"))
            items = data.get("items", [])
            return page, [str(it["series_id"]) for it in items if it.get("series_id")], data.get("count", 0)
    except Exception:
        return page, [], 0

def fetch_all_ids_for_genre(genre_def):
    gid = genre_def["id"]
    gname = genre_def["genre"]
    t0 = time.time()
    
    # 1. Get total count
    _, first_ids, total_count = fetch_genre_page(gname, 1)
    if total_count == 0:
        return gid, []
        
    total_pages = (total_count + 99) // 100
    all_ids = set(first_ids)
    
    if total_pages > 1:
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(fetch_genre_page, gname, p) for p in range(2, total_pages + 1)]
            for fut in as_completed(futures):
                _, ids, _ = fut.result()
                all_ids.update(ids)
                
    print(f"✓ {genre_def['name']} ({gname}): {len(all_ids):,} series fetched in {round(time.time() - t0, 2)}s")
    return gid, list(all_ids)

def main():
    print("=================================================================")
    print("🚀 Fetching & Indexing Authentic Categories for Hongguo Catalog...")
    print("=================================================================")
    t_start = time.time()
    
    genre_data = {}
    with ThreadPoolExecutor(max_workers=5) as g_executor:
        futures = {g_executor.submit(fetch_all_ids_for_genre, g): g for g in GENRE_MAP}
        for fut in as_completed(futures):
            gid, ids = fut.result()
            genre_data[gid] = ids
            
    print(f"\nAll genre mappings fetched in {round(time.time() - t_start, 2)}s.")
    print("Saving categories to SQLite database...")
    
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    
    # Create drama_categories relation table
    cur.execute("DROP TABLE IF EXISTS drama_categories")
    cur.execute("""
        CREATE TABLE drama_categories (
            drama_id TEXT,
            category_id TEXT,
            PRIMARY KEY (drama_id, category_id)
        )
    """)
    cur.execute("CREATE INDEX idx_dc_cat ON drama_categories(category_id)")
    cur.execute("CREATE INDEX idx_dc_drama ON drama_categories(drama_id)")
    
    cat_insert_batch = []
    # Also track tags update for each drama
    drama_tags_map = {}
    
    for gid, series_ids in genre_data.items():
        g_def = next(g for g in GENRE_MAP if g["id"] == gid)
        for sid in series_ids:
            drama_id = f"hg_{sid}"
            cat_insert_batch.append((drama_id, gid))
            cat_insert_batch.append((drama_id, "all"))
            
            if drama_id not in drama_tags_map:
                drama_tags_map[drama_id] = set()
            drama_tags_map[drama_id].add(g_def["name"])
            drama_tags_map[drama_id].add(g_def["genre"])
            
    # Also ensure Top 100 Leaderboard has categories
    cur.execute("SELECT id, title_cn FROM hongguo_dramas WHERE rank_num <= 100")
    for row in cur.fetchall():
        did, t_cn = row
        cat_insert_batch.append((did, "all"))
        if any(k in t_cn for k in ["逆袭", "话事", "老太", "婆婆", "丑小鸭", "富"]):
            cat_insert_batch.append((did, "urban_revenge"))
        if any(k in t_cn for k in ["总", "豪门", "首富", "富"]):
            cat_insert_batch.append((did, "billionaire_ceo"))
        if any(k in t_cn for k in ["皇子", "帝", "大唐", "太子", "侯府"]):
            cat_insert_batch.append((did, "palace_historical"))
        if any(k in t_cn for k in ["重生", "开学", "元婴"]):
            cat_insert_batch.append((did, "rebirth_travel"))
        if any(k in t_cn for k in ["喜欢", "爱", "妻"]):
            cat_insert_batch.append((did, "sweet_romance"))
            
    cur.executemany("INSERT OR IGNORE INTO drama_categories VALUES (?, ?)", cat_insert_batch)
    
    # Update primary category on hongguo_dramas table
    for gid, series_ids in genre_data.items():
        g_def = next(g for g in GENRE_MAP if g["id"] == gid)
        cur.executemany(
            f"UPDATE hongguo_dramas SET category = ?, category_id = ? WHERE id = ? AND (category_id = 'all' OR category_id IS NULL)",
            [(g_def["name"], gid, f"hg_{sid}") for sid in series_ids]
        )
        
    conn.commit()
    
    print("\n================ Category Distribution in Database ================")
    cur.execute("SELECT category_id, count(*) FROM drama_categories GROUP BY category_id ORDER BY count(*) DESC")
    for r in cur.fetchall():
        print(f"  Category '{r[0]}': {r[1]:,} dramas")
    print("=================================================================")
    conn.close()

if __name__ == "__main__":
    main()
