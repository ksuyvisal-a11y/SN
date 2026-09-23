import urllib.request
import re
import json

url = 'https://hongguodownloader.com/Browse'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
html = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')

print('HTML length:', len(html))

# Find script tags
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
print('Inline scripts count:', len(scripts))

src_scripts = re.findall(r'<script[^>]*src=["\']([^"\']+)["\']', html)
print('External scripts:', src_scripts)

# Look for URLs, json, endpoints
for idx, s in enumerate(scripts):
    if len(s.strip()) > 0:
        print(f"\n--- Script {idx} ({len(s)} chars) ---")
        lines = [line.strip() for line in s.split('\n') if any(k in line for k in ['fetch', 'http', '.json', 'catalog', 'leaderboard', 'api', '49', 'dramas'])]
        for l in lines[:20]:
            print("  ", l[:120])
