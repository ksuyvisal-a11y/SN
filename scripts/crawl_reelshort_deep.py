import urllib.request
import urllib.parse
import json
import re
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("DEEP REELSHORT CRAWLER: Sifting All Catalogues & Hidden Drama Repositories")
print("=" * 70)

BUILD_ID = "1790563283648"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.reelshort.com/',
    'Accept-Language': 'en-US,en;q=0.9',
}

# 1. Load existing dramas so we don't lose any already harvested
existing_dramas_path = Path("data/reelshort_all_dramas.json")
unique_books = {}
if existing_dramas_path.exists():
    try:
        with open(existing_dramas_path, 'r', encoding='utf-8') as f:
            for item in json.load(f):
                bid = item.get('book_id')
                if bid:
                    unique_books[bid] = item
    except Exception as e:
        print(f"Error loading existing dramas: {e}")

print(f"Starting with {len(unique_books)} already known ReelShort dramas.")

# 2. Comprehensive Search Keywords List
keywords_en = [
    # Alphabet letters
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
    'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
    # Common short words
    'the', 'my', 'me', 'her', 'his', 'him', 'she', 'he', 'we', 'our', 'in', 'to', 'for', 'with', 'on', 'at', 'by', 'from',
    # High-yield Romance & Drama tropes
    'love', 'billionaire', 'ceo', 'revenge', 'alpha', 'wolf', 'werewolf', 'vampire', 'mafia', 'dragon',
    'king', 'queen', 'prince', 'princess', 'secret', 'hidden', 'baby', 'triplets', 'twins', 'marriage',
    'married', 'wedding', 'divorce', 'ex', 'wife', 'husband', 'boss', 'contract', 'fake', 'forced',
    'mistress', 'cheat', 'betrayal', 'return', 'rebirth', 'second', 'chance', 'destiny', 'fate', 'mate',
    'luna', 'pack', 'moon', 'shadow', 'broken', 'heart', 'lies', 'kiss', 'night', 'sweet', 'dangerous',
    'forbidden', 'doctor', 'master', 'god', 'war', 'billion', 'heiress', 'tycoon', 'president', 'cold',
    'cruel', 'ruthless', 'sweetheart', 'temptation', 'seduction', 'game', 'rules', 'substitute', 'runaway',
    'bodyguard', 'daughter', 'son', 'mother', 'father', 'family', 'blood', 'bound', 'cage', 'demon', 'devil',
    'angel', 'fall', 'redemption', 'debt', 'rich', 'poor', 'maid', 'billionaire boss', 'secret billionaire',
    'contract marriage', 'alpha mate', 'wolf king', 'revenge return', 'ex wife', 'ex husband'
]

# Multilingual keywords for other languages
keywords_multi = [
    ('es', 'amor'), ('es', 'esposo'), ('es', 'esposa'), ('es', 'jefe'), ('es', 'venganza'), ('es', 'secreto'), ('es', 'boda'), ('es', 'divorcio'), ('es', 'lobo'), ('es', 'bebe'),
    ('pt', 'amor'), ('pt', 'esposo'), ('pt', 'esposa'), ('pt', 'chefe'), ('pt', 'vingança'), ('pt', 'segredo'), ('pt', 'casamento'), ('pt', 'divórcio'), ('pt', 'lobo'), ('pt', 'bebê'),
    ('ja', '愛'), ('ja', '社長'), ('ja', '復讐'), ('ja', '結婚'), ('ja', '離婚'), ('ja', '秘密'), ('ja', '転生'), ('ja', '狼'), ('ja', '契約'),
    ('zh-TW', '愛'), ('zh-TW', '總裁'), ('zh-TW', '復仇'), ('zh-TW', '結婚'), ('zh-TW', '離婚'), ('zh-TW', '秘密'), ('zh-TW', '重生'), ('zh-TW', '豪門'), ('zh-TW', '契約'),
    ('ko', '사랑'), ('ko', '대표'), ('ko', '복수'), ('ko', '결혼'), ('ko', '이혼'), ('ko', '비밀'), ('ko', '늑대'), ('ko', '계약'),
    ('id', 'cinta'), ('id', 'suami'), ('id', 'istri'), ('id', 'bos'), ('id', 'dendam'), ('id', 'rahasia'), ('id', 'nikah'), ('id', 'cerai'),
    ('fr', 'amour'), ('fr', 'mari'), ('fr', 'femme'), ('fr', 'patron'), ('fr', 'vengeance'), ('fr', 'secret'), ('fr', 'mariage'),
    ('de', 'liebe'), ('de', 'mann'), ('de', 'frau'), ('de', 'chef'), ('de', 'rache'), ('de', 'geheimnis'),
    ('ru', 'любовь'), ('ru', 'муж'), ('ru', 'жена'), ('ru', 'босс'), ('ru', 'месть'), ('ru', 'тайна'),
    ('th', 'รัก'), ('th', 'สามี'), ('th', 'ภรรยา'), ('th', 'บอส'), ('th', 'แค้น'), ('th', 'แต่งงาน'),
    ('vi', 'yêu'), ('vi', 'chồng'), ('vi', 'vợ'), ('vi', 'sếp'), ('vi', 'thù'), ('vi', 'kết hôn')
]

tasks = []
for kw in keywords_en:
    tasks.append(('en', kw))
for loc, kw in keywords_multi:
    tasks.append((loc, kw))

print(f"Total search keyword tasks prepared: {len(tasks)}")

def crawl_keyword(loc, kw):
    new_found = 0
    # Search page 1 first to check total pages
    encoded_kw = urllib.parse.quote(kw)
    base_url = f"https://www.reelshort.com/_next/data/{BUILD_ID}/{loc}/search.json?keywords={encoded_kw}"
    
    try:
        req = urllib.request.Request(base_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            pp = data.get('pageProps', {})
            total_pages = min(pp.get('totalPage', 1), 10) # crawl up to 10 pages per keyword
            books = pp.get('books', [])
            
            extracted = []
            for b in books:
                bid = b.get('book_id') or b.get('_id')
                if bid:
                    extracted.append((bid, b, loc))
            
            # Fetch remaining pages up to total_pages
            for page in range(2, total_pages + 1):
                p_url = f"{base_url}&page={page}"
                try:
                    p_req = urllib.request.Request(p_url, headers=HEADERS)
                    with urllib.request.urlopen(p_req, timeout=10) as p_resp:
                        p_data = json.loads(p_resp.read().decode('utf-8'))
                        p_books = p_data.get('pageProps', {}).get('books', [])
                        for b in p_books:
                            bid = b.get('book_id') or b.get('_id')
                            if bid:
                                extracted.append((bid, b, loc))
                except Exception:
                    pass
                time.sleep(0.05)
            
            return loc, kw, extracted
    except Exception as e:
        return loc, kw, []

# Execute concurrently
print("\nLaunching concurrent worker pool...")
with ThreadPoolExecutor(max_workers=8) as executor:
    futures = [executor.submit(crawl_keyword, loc, kw) for loc, kw in tasks]
    completed_count = 0
    for fut in as_completed(futures):
        loc, kw, items = fut.result()
        added_for_kw = 0
        for bid, b, b_loc in items:
            if bid not in unique_books:
                # Format properly
                title = b.get('book_title') or f"ReelShort Drama {bid}"
                poster = b.get('book_pic') or b.get('cover') or 'reelshort_logo.png'
                ch_count = int(b.get('chapter_count') or 40)
                desc = b.get('special_desc') or b.get('description') or ''
                reads = int(b.get('read_count') or 100000)
                first_ch = b.get('first_chapter_id') or '0001'
                
                # Clean slug
                clean_title = re.sub(r'[^a-zA-Z0-9]+', '-', title).strip('-').lower() or 'drama'
                slug = f"episode-1-{clean_title}-{bid}-{first_ch}"
                
                tags = [t.get('tag_name') for t in b.get('tag_list', []) if isinstance(t, dict) and t.get('tag_name')]
                
                unique_books[bid] = {
                    'book_id': str(bid),
                    'title': title,
                    'poster': poster,
                    'video_pic': poster,
                    'stream_url': '',
                    'chapter_count': ch_count,
                    'description': desc,
                    'locale': b_loc,
                    'first_chapter_id': first_ch,
                    'tags': tags,
                    'reads': reads,
                    'duration': 120,
                    'slug': slug
                }
                added_for_kw += 1
        completed_count += 1
        if added_for_kw > 0 or completed_count % 15 == 0:
            print(f"[{completed_count:3d}/{len(tasks)}] Keyword '{kw}' ({loc}): +{added_for_kw} new -> Total unique dramas: {len(unique_books)}")

print(f"\n============================================================")
print(f"TOTAL UNIQUE REELSHORT DRAMAS DISCOVERED: {len(unique_books)}")
print(f"============================================================")

# Save to data/reelshort_all_dramas.json
final_dramas = list(unique_books.values())
with open(existing_dramas_path, 'w', encoding='utf-8') as f:
    json.dump(final_dramas, f, ensure_ascii=False, indent=2)
print(f"Saved {len(final_dramas)} dramas to {existing_dramas_path}")

# Ingest into SQLite database data/hongguo_catalog.db
import sqlite3
db_path = Path("data/hongguo_catalog.db")
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("DELETE FROM hongguo_dramas WHERE platform_id = 'reelshort' OR platform = 'ReelShort'")
conn.commit()

for idx, item in enumerate(final_dramas):
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

# Print stats
cur.execute("SELECT platform, COUNT(*) FROM hongguo_dramas GROUP BY platform")
print("\n--- Final Platform Counts in Database ---")
for p, c in cur.fetchall():
    print(f"  {p}: {c}")

cur.execute("SELECT COUNT(*) FROM hongguo_dramas")
grand_total = cur.fetchone()[0]
print(f"GRAND TOTAL CATALOG: {grand_total}")
conn.close()
