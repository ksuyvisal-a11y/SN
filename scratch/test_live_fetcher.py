import urllib.request
import urllib.parse
import json
import sqlite3
import time
from pathlib import Path

DB_PATH = Path("data/hongguo_catalog.db")

def init_tables():
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS hongguo_dramas")
    cur.execute("""
        CREATE TABLE hongguo_dramas (
            id TEXT PRIMARY KEY,
            title TEXT,
            title_cn TEXT,
            title_kh TEXT,
            platform TEXT,
            platform_id TEXT,
            total_episodes INTEGER,
            category TEXT,
            category_id TEXT,
            rating TEXT,
            release_year TEXT,
            poster TEXT,
            description TEXT,
            tags TEXT,
            heat TEXT,
            status TEXT,
            rank_num INTEGER
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_hg_cat ON hongguo_dramas(category_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_hg_plat ON hongguo_dramas(platform_id)")
    conn.commit()
    conn.close()

def fetch_and_populate():
    init_tables()
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # 1. Fetch Top 100 Leaderboard (Matches Image 2 exactly!)
    print("[1] Fetching Top 100 Leaderboard from https://explorer.hongguodownloader.com/leaderboard ...")
    req = urllib.request.Request("https://explorer.hongguodownloader.com/leaderboard?board=hot&category=all&size=100", headers={"User-Agent": "Mozilla/5.0"})
    res = urllib.request.urlopen(req, timeout=10)
    lb_data = json.loads(res.read().decode("utf-8"))
    lb_items = lb_data.get("items", [])
    print(f"  Got {len(lb_items)} leaderboard dramas!")

    # Clear existing table to refresh with real catalog
    cur.execute("DELETE FROM hongguo_dramas")

    records = []
    for rank, item in enumerate(lb_items, 1):
        drama_id = f"hg_top_{rank:03d}"
        series_id = str(item.get("series_id") or "")
        title_cn = item.get("title", "Hongguo Drama").strip()
        eps = int(item.get("episode_cnt") or 80)
        if eps <= 0:
            eps = 80
        score = str(item.get("score") or "9.0")
        heat = str(item.get("heat") or "")
        cover = item.get("cover") or "posters/poster_sample_ceo.jpg"
        status = item.get("status") or "completed"

        title_kh = f"រឿងភាគពិសេស {title_cn}"
        full_title = f"《{title_cn}》 - {title_kh}"
        desc = f"រឿងភាគខ្លីពិសេស Hongguo (红果短剧) 《{title_cn}》 ចំណាត់ថ្នាក់លេខ {rank} នៅលើ Leaderboard កម្រិត 1080p Full HD សរុប {eps} ភាគ។"
        tags = json.dumps(["Leaderboard", f"Top {rank}", "Hot 100", "1080p Full HD"], ensure_ascii=False)

        records.append((
            drama_id,
            full_title,
            title_cn,
            title_kh,
            "Hongguo",
            "hongguo",
            eps,
            "All",
            "all",
            score,
            "2025",
            cover,
            desc,
            tags,
            heat,
            status,
            rank
        ))

    cur.executemany("INSERT OR REPLACE INTO hongguo_dramas VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", records)
    conn.commit()
    print(f"  Saved {len(records)} Leaderboard dramas into SQLite database!")

    # 2. Fetch pages of popular catalog dramas
    print("[2] Fetching popular catalog pages from https://explorer.hongguodownloader.com/explorer ...")
    total_fetched = len(records)
    for p in range(1, 11):
        try:
            url = f"https://explorer.hongguodownloader.com/explorer?page={p}&size=100&sort=popular"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            res = urllib.request.urlopen(req, timeout=10)
            data = json.loads(res.read().decode("utf-8"))
            items = data.get("items", [])
            page_records = []
            for item in items:
                series_id = str(item.get("series_id") or "")
                drama_id = f"hg_exp_{series_id}"
                title_cn = item.get("title", "").strip()
                if not title_cn:
                    continue
                eps = int(item.get("episode_cnt") or 80)
                if eps <= 0:
                    eps = 80
                score = str(item.get("score") or "8.8")
                cover = item.get("cover") or "posters/poster_sample_ceo.jpg"
                status = item.get("status") or "completed"
                heat = f"{item.get('play_cnt', 0):,}" if item.get('play_cnt') else ""

                title_kh = f"រឿងភាគ {title_cn}"
                full_title = f"《{title_cn}》 - {title_kh}"
                desc = f"រឿងភាគខ្លីពិសេស Hongguo 《{title_cn}》 មាន {eps} ភាគកម្រិត 1080p Full HD។"
                tags = json.dumps(["Popular", "Hongguo", "1080p"], ensure_ascii=False)

                page_records.append((
                    drama_id,
                    full_title,
                    title_cn,
                    title_kh,
                    "Hongguo",
                    "hongguo",
                    eps,
                    "Popular",
                    "popular",
                    score,
                    "2025",
                    cover,
                    desc,
                    tags,
                    heat,
                    status,
                    999
                ))

            cur.executemany("INSERT OR IGNORE INTO hongguo_dramas VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", page_records)
            conn.commit()
            total_fetched += len(page_records)
            print(f"  Page {p}/10: +{len(page_records)} dramas (Total saved: {total_fetched})")
        except Exception as e:
            print(f"  Page {p} error: {e}")

    conn.close()
    print(f"\nCOMPLETED! Total dramas saved in local SQLite: {total_fetched}")

if __name__ == "__main__":
    fetch_and_populate()
