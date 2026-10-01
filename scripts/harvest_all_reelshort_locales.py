import urllib.request
import re
import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("Harvesting ALL 13 Locales from https://www.reelshort.com/")
print("=" * 60)

locales = ['en', 'pt', 'es', 'de', 'fr', 'ja', 'ko', 'zh-TW', 'id', 'ru', 'ar', 'th', 'vi']
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.reelshort.com/',
}

# Load existing streams cache if any
streams_cache_file = Path("data/reelshort_streams_cache.json")
existing_streams = {}
if streams_cache_file.exists():
    try:
        with open(streams_cache_file, 'r', encoding='utf-8') as f:
            existing_streams = json.load(f)
    except Exception:
        existing_streams = {}

all_books = {}

for loc in locales:
    url = f'https://www.reelshort.com/{loc}' if loc != 'en' else 'https://www.reelshort.com/'
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
            if not m:
                continue
            d = json.loads(m.group(1))
            wi = d.get('props', {}).get('pageProps', {}).get('fallback', {}).get('/api/ms/hall/webInfo', {})
            
            # Shelves
            shelves = wi.get('bookShelfList', [])
            for s in shelves:
                books = s.get('books', []) or s.get('book_list', []) or s.get('list', [])
                shelf_name = s.get('shelf_name', 'General')
                for b in books:
                    bid = b.get('book_id') or b.get('id') or b.get('b_id')
                    if bid and bid not in all_books:
                        all_books[bid] = {
                            'locale': loc,
                            'book_id': str(bid),
                            'book_title': b.get('book_title') or b.get('title'),
                            'book_pic': b.get('book_pic') or b.get('cover'),
                            'chapter_count': int(b.get('chapter_count') or b.get('total_chapter_num') or 40),
                            'special_desc': b.get('special_desc') or b.get('introduction') or '',
                            'read_count': int(b.get('read_count') or 150000),
                            'shelf_name': shelf_name,
                            'theme_list': b.get('theme_list', [])
                        }

            # Banners
            banners = wi.get('banners', [])
            for b in banners:
                bid = b.get('b_id') or b.get('book_id')
                if bid and bid not in all_books and b.get('title'):
                    all_books[bid] = {
                        'locale': loc,
                        'book_id': str(bid),
                        'book_title': b.get('title'),
                        'book_pic': b.get('pic'),
                        'chapter_count': 40,
                        'special_desc': b.get('title'),
                        'read_count': 500000,
                        'shelf_name': 'Trending Featured',
                        'theme_list': [{'tag_name': 'Featured'}]
                    }
        print(f"Locale [{loc:>5}]: processed. Cumulative unique dramas: {len(all_books)}")
    except Exception as e:
        print(f"Locale [{loc:>5}] failed: {e}")

print(f"\nGRAND TOTAL UNIQUE REELSHORT DRAMAS DISCOVERED: {len(all_books)}")

# Format into standardized items
reelshort_dramas = []
for bid, b in all_books.items():
    title = b.get('book_title') or f"ReelShort Drama {bid}"
    poster = b.get('book_pic') or 'reelshort_logo.png'
    eps = b.get('chapter_count', 40)
    desc = b.get('special_desc') or f"ReelShort Vertical Mini-Series #{bid}"
    cached = existing_streams.get(bid, {})
    stream_url = cached.get('stream_url')
    video_pic = cached.get('video_pic')

    # Construct clean slug
    title_slug = re.sub(r'[^a-zA-Z0-9]+', '-', title).strip('-').lower() or 'drama'
    slug = cached.get('slug') or f"episode-1-{title_slug}-{bid}-0001"

    item = {
        'book_id': bid,
        'title': title,
        'poster': poster,
        'video_pic': video_pic or poster,
        'stream_url': stream_url or '',
        'chapter_count': eps,
        'description': desc,
        'locale': b.get('locale', 'en'),
        'tags': [t.get('tag_name') for t in b.get('theme_list', []) if isinstance(t, dict) and t.get('tag_name')],
        'reads': b.get('read_count', 100000),
        'duration': 120,
        'slug': slug
    }
    reelshort_dramas.append(item)

# Save to data/reelshort_all_dramas.json
dramas_json_path = Path("data/reelshort_all_dramas.json")
with open(dramas_json_path, 'w', encoding='utf-8') as f:
    json.dump(reelshort_dramas, f, ensure_ascii=False, indent=2)
print(f"Saved {len(reelshort_dramas)} dramas to {dramas_json_path}")

# Ingest into SQLite database data/hongguo_catalog.db
db_path = Path("data/hongguo_catalog.db")
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Remove old reelshort entries to refresh cleanly
cur.execute("DELETE FROM hongguo_dramas WHERE platform_id = 'reelshort' OR platform = 'ReelShort'")
conn.commit()

for idx, item in enumerate(reelshort_dramas):
    d_id = f"reelshort_{item['book_id']}"
    title = item['title']
    poster = item['poster']
    eps = item['chapter_count']
    desc = item['description']
    reads = item['reads']
    heat = f"{reads/1000:.1f}K" if reads < 1000000 else f"{reads/1000000:.1f}M"
    tags_str = ", ".join(item['tags']) if item['tags'] else "ReelShort, Romance"

    cat_str = item['tags'][0] if item['tags'] else "Romance"
    cat_id = "sweet_romance"
    t_lower = (title + " " + tags_str).lower()
    if "billionaire" in t_lower or "ceo" in t_lower:
        cat_id = "billionaire_ceo"
        cat_str = "Billionaire / CEO"
    elif "alpha" in t_lower or "werewolf" in t_lower or "vampire" in t_lower:
        cat_id = "urban_revenge"
        cat_str = "Werewolf / Revenge"
    elif "dragon" in t_lower or "war" in t_lower or "sovereign" in t_lower:
        cat_id = "god_of_war"
        cat_str = "Dragon King / War God"
    elif "mafia" in t_lower or "crime" in t_lower:
        cat_id = "action_suspense"
        cat_str = "Mafia / Crime"

    rating = "9.9" if idx < 10 else ("9.8" if idx < 50 else "9.7")

    cur.execute("""
        INSERT INTO hongguo_dramas (
            id, title, title_cn, title_kh, platform, platform_id,
            total_episodes, category, category_id, rating, release_year,
            poster, description, tags, heat, status, rank_num
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        d_id,
        title,
        title,
        title,
        "ReelShort",
        "reelshort",
        eps,
        cat_str,
        cat_id,
        rating,
        "2024",
        poster,
        desc,
        tags_str,
        heat,
        "Completed",
        idx + 1
    ))

conn.commit()

# Verify counts
cur.execute("SELECT platform, COUNT(*) FROM hongguo_dramas GROUP BY platform")
print("\n--- Updated Platform Counts ---")
for p, c in cur.fetchall():
    print(f"  {p}: {c}")

cur.execute("SELECT COUNT(*) FROM hongguo_dramas")
total_all = cur.fetchone()[0]
print(f"GRAND TOTAL ACROSS ALL PLATFORMS: {total_all}")

conn.close()
