with open("scratch/test_speechgen_js.py") as f:
    pass
import urllib.request, re

url = "https://speechgen.io/en/tts-khmer/"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
html = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=15).read().decode("utf-8")

# Search for uriTTS definition
matches = re.findall(r'.{0,50}uriTTS.{0,100}', html)
for m in matches:
    print("uriTTS match:", repr(m))

# Search for any ajax post to tts
matches2 = re.findall(r'.{0,50}\/index\.php\?r=tts.{0,100}', html)
for m in matches2:
    print("tts route match:", repr(m))
