import urllib.request, re

url = "https://speechgen.io/en/tts-khmer/"
headers = {"User-Agent": "Mozilla/5.0"}
html = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=15).read().decode("utf-8")

pos = html.find("function getTTsParams")
if pos != -1:
    print(html[pos:pos+1200])
else:
    print("getTTsParams not found, searching getTTs...")
    for m in re.finditer(r'getTTs[a-zA-Z0-9_]*', html):
        print(m.group(0))
