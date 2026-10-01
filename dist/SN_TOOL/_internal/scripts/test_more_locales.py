import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
headers = {'User-Agent': 'Mozilla/5.0'}

extra_locales = [
    ('it', 'amore'),
    ('it', 'marito'),
    ('tr', 'aşk'),
    ('tr', 'koca'),
    ('pl', 'miłość'),
    ('ro', 'dragoste'),
    ('cs', 'láska'),
    ('bg', 'любов')
]

for loc, kw in extra_locales:
    url = f'https://www.reelshort.com/_next/data/1790563283648/{loc}/search.json?keywords={urllib.parse.quote(kw)}'
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode('utf-8'))
            pp = data.get('pageProps', {})
            total = pp.get('total')
            total_pages = pp.get('totalPage')
            print(f"Locale [{loc:>4}] '{kw}': Total = {total}, Pages = {total_pages}")
    except Exception as e:
        print(f"Locale [{loc:>4}] '{kw}' error: {e}")
