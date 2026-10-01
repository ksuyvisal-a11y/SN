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
print("MASSIVE REELSHORT UNRESTRICTED CRAWLER (19 LOCALES + ALL PAGES)")
print("=" * 70)

BUILD_ID = "1790563283648"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.reelshort.com/',
    'Accept-Language': 'en-US,en;q=0.9',
}

# Load existing dramas
dramas_file = Path("data/reelshort_all_dramas.json")
unique_books = {}
if dramas_file.exists():
    try:
        with open(dramas_file, 'r', encoding='utf-8') as f:
            for item in json.load(f):
                bid = str(item.get('book_id'))
                if bid:
                    unique_books[bid] = item
    except Exception as e:
        print(f"Error loading existing: {e}")

print(f"Loaded {len(unique_books)} initial ReelShort dramas.")

# Prepare all query tasks
high_yield_keywords = [
    # Core English words & tropes
    'love', 'billionaire', 'ceo', 'revenge', 'husband', 'secret', 'marriage', 'wife', 'boss', 'ex',
    'baby', 'alpha', 'wolf', 'werewolf', 'vampire', 'mafia', 'dragon', 'king', 'queen', 'prince', 'princess',
    'wedding', 'divorce', 'contract', 'fake', 'forced', 'mistress', 'cheat', 'betrayal', 'return', 'rebirth',
    'second', 'chance', 'destiny', 'fate', 'luna', 'pack', 'moon', 'shadow', 'broken', 'heart', 'lies',
    'kiss', 'night', 'sweet', 'dangerous', 'forbidden', 'doctor', 'master', 'god', 'war', 'tycoon',
    'president', 'heiress', 'cold', 'cruel', 'ruthless', 'substitute', 'runaway', 'bodyguard', 'mother',
    'father', 'blood', 'demon', 'devil', 'maid', 'daughter', 'son', 'rich', 'poor', 'first', 'last',
    'hidden', 'triplets', 'twins', 'shackles', 'temptation', 'seduction', 'game', 'rules', 'bound',
    # Top 2-letter digraphs in English
    'th', 'he', 'in', 'er', 'an', 're', 'on', 'at', 'en', 'nd', 'ti', 'es', 'or', 'te', 'of', 'ed',
    'is', 'it', 'al', 'ar', 'st', 'to', 'nt', 'ng', 'se', 'ha', 'as', 'ou', 'io', 'le', 've', 'co',
    'me', 'de', 'hi', 'ri', 'ro', 'ic', 'ne', 'ea', 'ra', 'ce', 'li', 'ch', 'll', 'be', 'ma', 'si',
    'om', 'ur', 'wh', 'wi', 'sh', 'ab', 'ba', 'ca', 'da', 'fa', 'ga', 'ja', 'ka', 'la', 'pa', 'sa',
    'ta', 'va', 'wa', 'ya', 'za', 'bo', 'co', 'do', 'fo', 'go', 'ho', 'jo', 'ko', 'lo', 'mo', 'no',
    'po', 'so', 'to', 'vo', 'wo', 'yo', 'zo',
    # Numbers
    '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '18', '20', '24', '30', '50', '100'
]

# Multilingual queries across all other 18 locales
multilingual_tasks = [
    ('es', 'amor'), ('es', 'esposo'), ('es', 'esposa'), ('es', 'jefe'), ('es', 'venganza'), ('es', 'secreto'), ('es', 'boda'), ('es', 'divorcio'), ('es', 'lobo'), ('es', 'bebe'), ('es', 'bebé'), ('es', 'millonario'), ('es', 'hijo'),
    ('pt', 'amor'), ('pt', 'esposo'), ('pt', 'esposa'), ('pt', 'chefe'), ('pt', 'vingança'), ('pt', 'segredo'), ('pt', 'casamento'), ('pt', 'divórcio'), ('pt', 'lobo'), ('pt', 'bebê'), ('pt', 'bilionário'), ('pt', 'filho'),
    ('ja', '愛'), ('ja', '社長'), ('ja', '復讐'), ('ja', '結婚'), ('ja', '離婚'), ('ja', '秘密'), ('ja', '転生'), ('ja', '狼'), ('ja', '契約'), ('ja', '若様'), ('ja', '恋'), ('ja', '夫'), ('ja', '妻'),
    ('zh-TW', '愛'), ('zh-TW', '總裁'), ('zh-TW', '復仇'), ('zh-TW', '結婚'), ('zh-TW', '離婚'), ('zh-TW', '秘密'), ('zh-TW', '重生'), ('zh-TW', '豪門'), ('zh-TW', '契約'), ('zh-TW', '少爺'), ('zh-TW', '千金'), ('zh-TW', '前夫'), ('zh-TW', '前妻'),
    ('ko', '사랑'), ('ko', '대표'), ('ko', '복수'), ('ko', '결혼'), ('ko', '이혼'), ('ko', '비밀'), ('ko', '늑대'), ('ko', '계약'), ('ko', '남편'), ('ko', '아내'), ('ko', '재벌'),
    ('id', 'cinta'), ('id', 'suami'), ('id', 'istri'), ('id', 'bos'), ('id', 'dendam'), ('id', 'rahasia'), ('id', 'nikah'), ('id', 'cerai'), ('id', 'anak'), ('id', 'miliarder'),
    ('fr', 'amour'), ('fr', 'mari'), ('fr', 'femme'), ('fr', 'patron'), ('fr', 'vengeance'), ('fr', 'secret'), ('fr', 'mariage'), ('fr', 'milliardaire'), ('fr', 'enfant'),
    ('de', 'liebe'), ('de', 'mann'), ('de', 'frau'), ('de', 'chef'), ('de', 'rache'), ('de', 'geheimnis'), ('de', 'hochzeit'), ('de', 'milliardär'), ('de', 'kind'),
    ('ru', 'любовь'), ('ru', 'муж'), ('ru', 'жена'), ('ru', 'босс'), ('ru', 'месть'), ('ru', 'тайна'), ('ru', 'свадьба'), ('ru', 'миллиардер'),
    ('th', 'รัก'), ('th', 'สามี'), ('th', 'ภรรยา'), ('th', 'บอส'), ('th', 'แค้น'), ('th', 'แต่งงาน'), ('th', 'ความลับ'), ('th', 'มหาเศรษฐี'),
    ('vi', 'yêu'), ('vi', 'chồng'), ('vi', 'vợ'), ('vi', 'sếp'), ('vi', 'thù'), ('vi', 'kết hôn'), ('vi', 'bí mật'), ('vi', 'tỷ phú'),
    ('it', 'amore'), ('it', 'marito'), ('it', 'moglie'), ('it', 'capo'), ('it', 'vendetta'), ('it', 'segreto'), ('it', 'matrimonio'), ('it', 'miliardario'),
    ('tr', 'aşk'), ('tr', 'koca'), ('tr', 'karı'), ('tr', 'patron'), ('tr', 'intikam'), ('tr', 'sır'), ('tr', 'evlilik'), ('tr', 'milyarder'),
    ('pl', 'miłość'), ('pl', 'mąż'), ('pl', 'żona'), ('pl', 'szef'), ('pl', 'zemsta'), ('pl', 'sekret'), ('pl', 'małżeństwo'), ('pl', 'miliarder'),
    ('ro', 'dragoste'), ('ro', 'soț'), ('ro', 'soție'), ('ro', 'șef'), ('ro', 'răzbunare'), ('ro', 'secret'), ('ro', 'căsătorie'),
    ('cs', 'láska'), ('cs', 'manžel'), ('cs', 'manželka'), ('cs', 'šéf'), ('cs', 'pomsta'), ('cs', 'tajemství'), ('cs', 'manželství'),
    ('bg', 'любов'), ('bg', 'съпруг'), ('bg', 'съпруга'), ('bg', 'шеф'), ('bg', 'отмъщение'), ('bg', 'тайна'), ('bg', 'брак'),
    ('ar', 'حب'), ('ar', 'زوج'), ('ar', 'زوجة'), ('ar', 'مدير'), ('ar', 'انتقام'), ('ar', 'سر'), ('ar', 'زواج'), ('ar', 'ملياردير')
]

all_tasks = []
for kw in high_yield_keywords:
    all_tasks.append(('en', kw))
for loc, kw in multilingual_tasks:
    all_tasks.append((loc, kw))

print(f"Total search tasks queued: {len(all_tasks)}")

def crawl_task(loc, kw):
    encoded_kw = urllib.parse.quote(kw)
    base_url = f"https://www.reelshort.com/_next/data/{BUILD_ID}/{loc}/search.json?keywords={encoded_kw}"
    extracted = []
    
    try:
        req = urllib.request.Request(base_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            pp = data.get('pageProps', {})
            total_pages = min(pp.get('totalPage', 1), 50) # CRAWL UP TO 50 FULL PAGES PER KEYWORD!
            books = pp.get('books', [])
            
            for b in books:
                bid = b.get('book_id') or b.get('_id')
                if bid:
                    extracted.append((str(bid), b, loc))
            
            for p in range(2, total_pages + 1):
                p_url = f"{base_url}&page={p}"
                try:
                    p_req = urllib.request.Request(p_url, headers=HEADERS)
                    with urllib.request.urlopen(p_req, timeout=10) as p_resp:
                        p_data = json.loads(p_resp.read().decode('utf-8'))
                        for b in p_data.get('pageProps', {}).get('books', []):
                            bid = b.get('book_id') or b.get('_id')
                            if bid:
                                extracted.append((str(bid), b, loc))
                except Exception:
                    pass
                time.sleep(0.04)
                
            return loc, kw, extracted
    except Exception as e:
        return loc, kw, []

# Execute concurrently with 10 workers
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(crawl_task, loc, kw) for loc, kw in all_tasks]
    done = 0
    for fut in as_completed(futures):
        loc, kw, items = fut.result()
        new_cnt = 0
        for bid, b, b_loc in items:
            if bid not in unique_books:
                title = b.get('book_title') or f"ReelShort Drama {bid}"
                poster = b.get('book_pic') or b.get('cover') or 'reelshort_logo.png'
                ch_count = int(b.get('chapter_count') or 40)
                desc = b.get('special_desc') or b.get('description') or ''
                reads = int(b.get('read_count') or 100000)
                first_ch = b.get('first_chapter_id') or '0001'
                
                clean_title = re.sub(r'[^a-zA-Z0-9]+', '-', title).strip('-').lower() or 'drama'
                slug = f"episode-1-{clean_title}-{bid}-{first_ch}"
                tags = [t.get('tag_name') for t in b.get('tag_list', []) if isinstance(t, dict) and t.get('tag_name')]
                
                unique_books[bid] = {
                    'book_id': bid,
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
                new_cnt += 1
        done += 1
        if new_cnt > 0 or done % 20 == 0:
            print(f"[{done:3d}/{len(all_tasks)}] '{kw}' ({loc}): +{new_cnt} -> Current Grand Total: {len(unique_books)} dramas", flush=True)

print(f"\n============================================================")
print(f"FINAL TOTAL UNIQUE REELSHORT DRAMAS DISCOVERED: {len(unique_books)}")
print(f"============================================================")

# Save to data/reelshort_all_dramas.json
final_list = list(unique_books.values())
with open(dramas_file, 'w', encoding='utf-8') as f:
    json.dump(final_list, f, ensure_ascii=False, indent=2)
print(f"Saved {len(final_list)} dramas to {dramas_file}")

# Update SQLite Database
import sqlite3
db_file = Path("data/hongguo_catalog.db")
conn = sqlite3.connect(db_file)
cur = conn.cursor()

cur.execute("DELETE FROM hongguo_dramas WHERE platform_id = 'reelshort' OR platform = 'ReelShort'")
conn.commit()

for idx, item in enumerate(final_list):
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

cur.execute("SELECT platform, COUNT(*) FROM hongguo_dramas GROUP BY platform")
print("\n--- Final Platform Counts in Database ---")
for p, c in cur.fetchall():
    print(f"  {p}: {c}")

cur.execute("SELECT COUNT(*) FROM hongguo_dramas")
grand_total = cur.fetchone()[0]
print(f"GRAND TOTAL CATALOG: {grand_total}")
conn.close()
