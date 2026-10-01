import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
headers = {'User-Agent': 'Mozilla/5.0'}

keywords = ['e', 'i', 'o', 'u', 'y', 'me', 'my', 'wife', 'husband', 'boss', 'ceo', 'alpha', 'wolf', 'love', 'revenge', 'marriage', 'secret']

for kw in keywords:
    url = f'https://www.reelshort.com/_next/data/1790563283648/en/search.json?keywords={kw}'
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode('utf-8'))
            pp = data.get('pageProps', {})
            total = pp.get('total')
            total_pages = pp.get('totalPage')
            print(f"Keyword '{kw:>10}': Total = {total}, TotalPages = {total_pages}")
    except Exception as e:
        print(f"Keyword '{kw:>10}' error: {e}")
