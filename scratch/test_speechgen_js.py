with open("scratch/test_speechgen_js.py") as f:
    pass
import urllib.request, re

url = "https://speechgen.io/en/tts-khmer/"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
html = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=15).read().decode("utf-8")

for m in re.finditer(r'(?:uriTTS|uriSite|cptch)[^\n;]+', html):
    print("LINE:", m.group(0)[:120])
