import urllib.request, re

url = "https://speechgen.io/en/tts-khmer/"
headers = {"User-Agent": "Mozilla/5.0"}
html = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=15).read().decode("utf-8")

pos = html.find("function getTTsParams")
print(html[pos+1000:pos+3000])
