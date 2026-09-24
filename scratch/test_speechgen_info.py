import urllib.request
import re

url = "https://speechgen.io/en/tts-khmer/"
headers = {"User-Agent": "Mozilla/5.0"}
html = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=15).read().decode("utf-8")

for m in re.finditer(r"voice_0[12]_[^\"'\s]+", html):
    pos = m.start()
    print("MATCH AT POS", pos)
    print(html[pos-120:pos+350])
    print("="*60)
