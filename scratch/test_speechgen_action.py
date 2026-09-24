import urllib.request, re

url = "https://speechgen.io/en/tts-khmer/"
headers = {"User-Agent": "Mozilla/5.0"}
html = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=15).read().decode("utf-8")

pos = html.find("recAction")
while pos != -1:
    print("--- recAction at", pos, "---")
    print(html[max(0, pos-200):min(len(html), pos+400)])
    pos = html.find("recAction", pos + 1)
