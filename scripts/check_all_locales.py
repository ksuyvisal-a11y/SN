import urllib.request
import re
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

locales = ['en', 'pt', 'es', 'de', 'fr', 'ja', 'ko', 'zh-TW', 'id', 'ru', 'ar', 'th', 'vi']
all_books = {}

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

for loc in locales:
    url = f'https://www.reelshort.com/{loc}' if loc != 'en' else 'https://www.reelshort.com/'
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode('utf-8', errors='ignore')
            m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
            if m:
                d = json.loads(m.group(1))
                wi = d.get('props', {}).get('pageProps', {}).get('fallback', {}).get('/api/ms/hall/webInfo', {})
                shelves = wi.get('bookShelfList', [])
                loc_books = 0
                for s in shelves:
                    b_list = s.get('books', []) or s.get('book_list', []) or s.get('list', [])
                    for b in b_list:
                        bid = b.get('book_id') or b.get('id') or b.get('b_id')
                        if bid and bid not in all_books:
                            all_books[bid] = b
                            loc_books += 1
                banners = wi.get('banners', [])
                for b in banners:
                    bid = b.get('b_id') or b.get('book_id')
                    if bid and bid not in all_books and b.get('title'):
                        all_books[bid] = b
                        loc_books += 1
                print(f"Locale '{loc}': added {loc_books} new books -> Total unique so far: {len(all_books)}")
    except Exception as e:
        print(f"Locale '{loc}' error: {e}")

print(f"\nGRAND TOTAL UNIQUE REELSHORT DRAMAS FOUND: {len(all_books)}")
