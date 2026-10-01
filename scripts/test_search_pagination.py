import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
headers = {'User-Agent': 'Mozilla/5.0'}

url = 'https://www.reelshort.com/_next/data/1790563283648/en/search.json?keywords=love&page=2'
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=10) as r:
    data = json.loads(r.read().decode('utf-8'))
    pp = data.get('pageProps', {})
    books = pp.get('books', [])
    print(f"Page 2: Total={pp.get('total')}, TotalPage={pp.get('totalPage')}, Books={len(books)}")
    if books:
        print("Page 2 First Book:", books[0].get('book_title'), "(ID:", books[0].get('book_id'), ")")
