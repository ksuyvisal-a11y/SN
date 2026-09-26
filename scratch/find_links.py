import urllib.request
import re

headers = {'User-Agent': 'Mozilla/5.0'}
with urllib.request.urlopen(urllib.request.Request('https://hongguodownloader.com/', headers=headers), timeout=10) as res:
    html = res.read().decode('utf-8', errors='ignore')

links = re.findall(r'href=[\"\']([^\"\']+)[\"\']', html)
for l in sorted(set(links)):
    print(l)
