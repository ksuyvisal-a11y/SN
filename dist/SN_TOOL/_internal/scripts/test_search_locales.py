import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
headers = {'User-Agent': 'Mozilla/5.0'}

locales_test = [
    ('es', 'amor'),
    ('es', 'esposo'),
    ('pt', 'amor'),
    ('pt', 'esposo'),
    ('ja', '愛'),
    ('ja', '社長'),
    ('zh-TW', '愛'),
    ('zh-TW', '總裁'),
    ('ko', '사랑'),
    ('id', 'cinta'),
    ('fr', 'amour'),
    ('de', 'liebe'),
    ('ru', 'любовь'),
    ('th', 'รัก'),
    ('vi', 'yêu')
]

for loc, kw in locales_test:
    url = f'https://www.reelshort.com/_next/data/1790563283648/{loc}/search.json?keywords={urllib.parse.quote(kw)}'
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode('utf-8'))
            pp = data.get('pageProps', {})
            total = pp.get('total')
            total_pages = pp.get('totalPage')
            print(f"Locale [{loc:>5}] '{kw}': Total = {total}, Pages = {total_pages}")
    except Exception as e:
        print(f"Locale [{loc:>5}] '{kw}' error: {e}")
