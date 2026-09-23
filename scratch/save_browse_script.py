import urllib.request
import re
import json

url = 'https://hongguodownloader.com/Browse'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
html = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')

scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
with open('scratch/browse_script.js', 'w', encoding='utf-8') as f:
    f.write(scripts[2])

print('Saved scratch/browse_script.js, length:', len(scripts[2]))
