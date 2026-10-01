import urllib.request
import re
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
headers = {'User-Agent': 'Mozilla/5.0'}

test_urls = [
    'https://www.reelshort.com/search?keywords=love',
    'https://www.reelshort.com/search?keywords=the',
    'https://www.reelshort.com/search?keywords=billionaire',
    'https://www.reelshort.com/search?keywords=a',
    'https://www.reelshort.com/search?keywords=',
    'https://www.reelshort.com/_next/data/1790563283648/en/search.json?keywords=love',
    'https://www.reelshort.com/_next/data/1790563283648/en/search.json?keywords=the'
]

for u in test_urls:
    try:
        req = urllib.request.Request(u, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            body = r.read().decode('utf-8', errors='ignore')
            if 'search.json' in u:
                data = json.loads(body)
                pp = data.get('pageProps', {})
            else:
                m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', body)
                d = json.loads(m.group(1)) if m else {}
                pp = d.get('props', {}).get('pageProps', {})
            total = pp.get('total')
            books = pp.get('books', [])
            print(f"URL: {u}")
            print(f"  Total: {total}, Books returned: {len(books)}")
            if books:
                print(f"  First: {books[0].get('book_title')} (ID: {books[0].get('book_id')})")
    except Exception as e:
        print(f"URL {u} failed: {e}")
