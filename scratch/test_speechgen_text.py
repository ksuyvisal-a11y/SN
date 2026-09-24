import urllib.request, re

url = "https://speechgen.io/en/tts-khmer/"
headers = {"User-Agent": "Mozilla/5.0"}
html = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=15).read().decode("utf-8")

textarea = re.findall(r'<textarea[^>]*>(.*?)</textarea>', html, re.DOTALL)
khmer_matches = re.findall(r'[\u1780-\u17ff\s\.,!?។៕]+', html)

out_lines = []
for t in textarea:
    out_lines.append(f"TEXTAREA: {t.strip()}")

for km in khmer_matches:
    if len(km.strip()) > 10:
        out_lines.append(f"KM: {km.strip()}")

with open("scratch/speechgen_khmer_text.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines))
print("Saved", len(out_lines), "lines to scratch/speechgen_khmer_text.txt")
