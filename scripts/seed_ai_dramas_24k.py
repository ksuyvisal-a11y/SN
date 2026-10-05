"""
Seed 24,081 Authentic AI Dramas from data/ai_dramas_streams.json into data/hongguo_catalog.db
"""
import sys
import os
import json
import sqlite3
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

DB_PATH = Path("data/hongguo_catalog.db")
AI_STREAMS_PATH = Path("data/ai_dramas_streams.json")
TARGET_COUNT = 24081

def main():
    print(f"🚀 Initializing AI Dramas Seeder (Target: {TARGET_COUNT:,})...")
    if not AI_STREAMS_PATH.exists():
        print(f"Error: {AI_STREAMS_PATH} does not exist!")
        return

    with open(AI_STREAMS_PATH, "r", encoding="utf-8") as f:
        streams = json.load(f)

    print(f"Loaded {len(streams):,} items from ai_dramas_streams.json.")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("DELETE FROM hongguo_dramas WHERE platform_id = 'ai_drama' OR platform = 'AI Dramas'")
    cur.execute("DELETE FROM drama_categories WHERE drama_id LIKE 'ai_%'")
    conn.commit()

    records = []
    cat_records = []
    rank = 1

    for key, it in streams.items():
        if rank > TARGET_COUNT:
            break
        
        drama_id = key if key.startswith("ai_") else f"ai_{key}"
        title_cn = it.get("title") or f"AI Drama #{rank}"
        title = f"《{title_cn}》"
        title_kh = f"រឿង AI កំពូល {title_cn}"
        poster = it.get("poster") or ""
        desc = it.get("description") or "រឿងភាគខ្លី AI ចិន (Chinese AI Short Drama) កម្រិត 1080p Full HD សំឡេងច្បាស់ត្រជាក់ភ្នែក។"
        
        # Calculate episode count from play_url
        play_url = it.get("play_url", "")
        if play_url:
            eps_count = len([x for x in play_url.split("#") if x.strip()])
        else:
            eps_count = 1
        if eps_count < 1: eps_count = 1

        heat = it.get("heat") or f"{8000 + (rank * 17 % 20000)}万"
        score = f"{9.0 + (rank % 10) * 0.1:.1f}"
        tags = json.dumps(["AI", "AI漫剧", "Chinese AI", "1080p Full HD", "រឿង AI ចិន"], ensure_ascii=False)

        records.append((
            drama_id,
            title,
            title_cn,
            title_kh,
            "AI Dramas",
            "ai_drama",
            eps_count,
            "AI",
            "ai_drama",
            score,
            "2025",
            poster,
            desc,
            tags,
            heat,
            "completed",
            rank
        ))

        cat_records.append((drama_id, "all"))
        cat_records.append((drama_id, "ai_drama"))

        rank += 1

        if len(records) >= 5000:
            cur.executemany("INSERT OR REPLACE INTO hongguo_dramas VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", records)
            cur.executemany("INSERT OR IGNORE INTO drama_categories VALUES (?, ?)", cat_records)
            conn.commit()
            print(f"  -> Ingested {rank-1:,} / {TARGET_COUNT:,} AI Dramas...")
            records = []
            cat_records = []

    if records:
        cur.executemany("INSERT OR REPLACE INTO hongguo_dramas VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", records)
        cur.executemany("INSERT OR IGNORE INTO drama_categories VALUES (?, ?)", cat_records)
        conn.commit()
        print(f"  -> Ingested final batch up to {rank-1:,} AI Dramas.")

    cur.execute("SELECT count(*) FROM hongguo_dramas WHERE platform_id = 'ai_drama'")
    cnt = cur.fetchone()[0]
    print(f"✅ SUCCESS: AI Dramas count in DB: {cnt:,}")
    cur.execute("SELECT count(*) FROM hongguo_dramas")
    tot = cur.fetchone()[0]
    print(f"✅ Total dramas across all platforms in DB: {tot:,}")
    conn.close()

if __name__ == "__main__":
    main()
