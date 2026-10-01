import urllib.request
import re
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
headers = {'User-Agent': 'Mozilla/5.0'}
all_books = {}
locales = ['en', 'pt', 'es', 'de', 'fr', 'ja', 'ko', 'zh-TW', 'id', 'ru', 'ar', 'th', 'vi']

for loc in locales:
    url = f'https://www.reelshort.com/{loc}' if loc != 'en' else 'https://www.reelshort.com/'
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode('utf-8', errors='ignore')
            m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
            if m:
                d = json.loads(m.group(1))
                wi = d.get('props', {}).get('pageProps', {}).get('fallback', {}).get('/api/ms/hall/webInfo', {})
                shelves = wi.get('bookShelfList', [])
                if shelves and shelves[0].get('books') and loc == 'en':
                    print("Sample book keys:", list(shelves[0]['books'][0].keys()))
                    print("Sample book:", json.dumps(shelves[0]['books'][0], indent=2))
                for s in shelves:
                    for b in s.get('books', []) or s.get('book_list', []) or s.get('list', []):
                        bid = b.get('book_id') or b.get('id') or b.get('b_id')
                        if bid and bid not in all_books:
                            all_books[bid] = {
                                'locale': loc,
                                'book_id': bid,
                                'title': b.get('book_title') or b.get('title'),
                                'cover': b.get('book_pic') or b.get('cover'),
                                'chapter_count': b.get('chapter_count') or b.get('total_chapter_num') or 40,
                                'special_desc': b.get('special_desc', '')
                            }
    except Exception as e:
        print(f"Error {loc}: {e}")

print(f"Total unique books across all locales: {len(all_books)}")

# Check some samples
for loc in ['en', 'ja', 'es', 'zh-TW', 'pt']:
    matching = [v for v in all_books.values() if v['locale'] == loc]
    print(f"\n--- Sample from locale {loc} (Total in {loc}: {len(matching)}) ---")
    for b in matching[:3]:
        print(f"  [{b['book_id']}] {b['title']} (Episodes: {b['chapter_count']}, Cover: {b['cover'][:40] if b.get('cover') else 'None'}...)")
