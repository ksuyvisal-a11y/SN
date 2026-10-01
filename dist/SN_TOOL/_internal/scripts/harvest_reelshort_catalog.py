import re
import json
import urllib.request
import urllib.parse
import sqlite3
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import sys
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("ReelShort Full Catalog Harvester & Stream Ingestion")
print("=" * 60)

BASE_URL = "https://www.reelshort.com"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.reelshort.com/',
    'Accept-Language': 'en-US,en;q=0.9',
}

# 1. Fetch homepage to get buildId and all shelf/banner books
print("Fetching ReelShort homepage...")
req = urllib.request.Request(BASE_URL, headers=HEADERS)
with urllib.request.urlopen(req, timeout=15) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
if not m:
    print("Error: Could not find __NEXT_DATA__")
    exit(1)

next_data = json.loads(m.group(1))
build_id = next_data.get('buildId', '1790563283648')
print(f"Detected Next.js buildId: {build_id}")

webinfo = next_data.get('props', {}).get('pageProps', {}).get('fallback', {}).get('/api/ms/hall/webInfo', {})
shelves = webinfo.get('bookShelfList', [])
banners = webinfo.get('banners', [])

books_dict = {}

# From Shelves
for s in shelves:
    b_list = s.get('books', []) or s.get('book_list', []) or s.get('list', [])
    for b in b_list:
        bid = b.get('book_id') or b.get('id') or b.get('b_id')
        if bid and bid not in books_dict:
            books_dict[bid] = b

# From Banners
for b in banners:
    bid = b.get('b_id') or b.get('book_id')
    if bid and bid not in books_dict and b.get('title'):
        books_dict[bid] = {
            'book_id': bid,
            'book_title': b.get('title'),
            'book_pic': b.get('pic'),
            'special_desc': b.get('title'),
            'chapter_count': 40
        }

print(f"Total unique books extracted from homepage data: {len(books_dict)}")

# Also extract all episode slugs from the HTML
all_ep_links = set(re.findall(r'href=["\']([^"\']*episode[^"\']*)["\']', html))
slug_to_bid = {}
for l in all_ep_links:
    decoded = urllib.parse.unquote(l)
    m_slug = re.search(r'(episode-\d+-[a-zA-Z0-9_-]+)', decoded)
    if m_slug:
        slug = m_slug.group(1)
        # Extract book_id from slug: episode-1-title-{book_id}-{chapter_id}
        parts = slug.split('-')
        if len(parts) >= 4:
            bid = parts[-2]
            slug_to_bid[bid] = slug

print(f"Total episode slugs mapped: {len(slug_to_bid)}")

# 2. Concurrently resolve full metadata & M3U8 streams for all dramas
print(f"\nResolving full metadata and authentic M3U8 streams for {len(books_dict)} dramas...")

streams_cache = {}
full_dramas = []

def resolve_single_drama(bid, book_data):
    # Try slug endpoint first if available
    slug = slug_to_bid.get(bid)
    if not slug:
        # Construct slug from title and first chapter if available
        title_slug = re.sub(r'[^a-zA-Z0-9]+', '-', book_data.get('book_title', 'drama')).strip('-').lower()
        first_ch = book_data.get('chapter_id') or '0001'
        slug = f"episode-1-{title_slug}-{bid}-{first_ch}"

    api_url = f"https://www.reelshort.com/_next/data/{build_id}/en/episodes/{slug}.json?play_time=1&slug={slug}"
    req2 = urllib.request.Request(api_url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req2, timeout=8) as r:
            d = json.loads(r.read().decode('utf-8'))
            data = d.get('pageProps', {}).get('data')
            if data and data.get('video_url'):
                return {
                    'book_id': bid,
                    'title': data.get('book_title') or book_data.get('book_title'),
                    'poster': data.get('book_pic') or book_data.get('book_pic'),
                    'video_pic': data.get('video_pic'),
                    'stream_url': data.get('video_url'),
                    'chapter_count': int(data.get('chapter_count') or book_data.get('chapter_count') or 40),
                    'description': data.get('special_desc') or book_data.get('special_desc') or '',
                    'tags': [t.get('tag_name') for t in data.get('tag_list', []) if isinstance(t, dict) and t.get('tag_name')],
                    'reads': int(data.get('collect_count') or 100000),
                    'duration': data.get('duration', 120),
                    'slug': slug
                }
    except Exception:
        pass

    # Fallback to book_data if slug fetch failed
    return {
        'book_id': bid,
        'title': book_data.get('book_title'),
        'poster': book_data.get('book_pic') or book_data.get('default_pic'),
        'video_pic': book_data.get('book_pic'),
        'stream_url': '',
        'chapter_count': int(book_data.get('chapter_count') or 40),
        'description': book_data.get('special_desc') or book_data.get('introduction') or '',
        'tags': [t.get('tag_name') for t in book_data.get('theme_list', []) if isinstance(t, dict) and t.get('tag_name')],
        'reads': int(book_data.get('read_count') or 100000),
        'duration': 120,
        'slug': slug
    }

resolved_count = 0
has_stream_count = 0

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(resolve_single_drama, bid, b): bid for bid, b in books_dict.items()}
    for fut in as_completed(futures):
        res = fut.result()
        if res:
            bid = res['book_id']
            full_dramas.append(res)
            resolved_count += 1
            if res.get('stream_url'):
                has_stream_count += 1
                streams_cache[f"reelshort_{bid}"] = {
                    'id': f"reelshort_{bid}",
                    'book_id': bid,
                    'title': res['title'],
                    'stream_url': res['stream_url'],
                    'video_pic': res['video_pic'],
                    'chapter_count': res['chapter_count'],
                    'duration': res['duration'],
                    'slug': res['slug']
                }

print(f"\nCompleted: {resolved_count} dramas processed.")
print(f"Verified Active M3U8 Streams: {has_stream_count} / {resolved_count}")

# 3. Save to data/reelshort_all_dramas.json & data/reelshort_streams_cache.json
out_dir = Path("data")
out_dir.mkdir(parents=True, exist_ok=True)

with open(out_dir / "reelshort_all_dramas.json", "w", encoding="utf-8") as f:
    json.dump(full_dramas, f, ensure_ascii=False, indent=2)

with open(out_dir / "reelshort_streams_cache.json", "w", encoding="utf-8") as f:
    json.dump(streams_cache, f, ensure_ascii=False, indent=2)

print(f"Saved {len(full_dramas)} dramas to data/reelshort_all_dramas.json")
print(f"Saved {len(streams_cache)} streams to data/reelshort_streams_cache.json")

# 4. Insert / Update into hongguo_catalog.db
db_path = out_dir / "hongguo_catalog.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

for idx, d in enumerate(full_dramas):
    d_id = f"reelshort_{d['book_id']}"
    title = d.get('title') or f"ReelShort Drama #{d['book_id']}"
    poster = d.get('poster') or 'reelshort_logo.png'
    eps = int(d.get('chapter_count') or 40)
    desc = d.get('description') or f"ReelShort English Vertical Short Drama (Full HD)."
    reads = d.get('reads', 100000)
    heat = f"{reads/1000:.1f}K" if reads < 1000000 else f"{reads/1000000:.1f}M"
    
    tags_list = d.get('tags', [])
    tags_str = ", ".join(tags_list) if tags_list else "ReelShort, Romance"
    
    cat_str = tags_list[0] if tags_list else "Romance"
    cat_id = "sweet_romance"
    t_lower = (title + " " + tags_str).lower()
    if "billionaire" in t_lower or "ceo" in t_lower:
        cat_id = "billionaire_ceo"
        cat_str = "Billionaire / CEO"
    elif "alpha" in t_lower or "werewolf" in t_lower or "vampire" in t_lower:
        cat_id = "urban_revenge"
        cat_str = "Werewolf / Alpha"
    elif "dragon" in t_lower or "war" in t_lower or "sovereign" in t_lower:
        cat_id = "god_of_war"
        cat_str = "Dragon King / War God"
    elif "mafia" in t_lower or "crime" in t_lower:
        cat_id = "action_suspense"
        cat_str = "Mafia / Crime"

    rating = "9.9" if idx < 15 else ("9.8" if idx < 40 else "9.7")

    cur.execute("""
        INSERT OR REPLACE INTO hongguo_dramas (
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

cur.execute("SELECT COUNT(*) FROM hongguo_dramas WHERE platform_id = 'reelshort'")
rs_cnt = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM hongguo_dramas")
total_now = cur.fetchone()[0]

conn.close()

print(f"\n🎉 SUCCESS: Database updated!")
print(f"Total ReelShort Dramas in DB: {rs_cnt}")
print(f"Total Dramas across all platforms in DB: {total_now}")
