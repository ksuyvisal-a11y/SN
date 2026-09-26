import urllib.request
import re
import json

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
url = 'https://hongguodownloader.com/drama/7683196130645003288'
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=10) as res:
        html = res.read().decode('utf-8', errors='ignore')
        print(f"Status: {res.status}, Length: {len(html)}")
        links = re.findall(r'https?://[^\s"\'<>]+', html)
        video_urls = [u for u in links if any(k in u.lower() for k in ['.m3u8', '.mp4', 'api', 'stream', 'video', 'play'])]
        print("Matching links in drama page:", video_urls[:15])
        
        # Check script tags or JSON-LD or state
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
        for s in scripts:
            if '7683196130645003288' in s or 'series' in s or 'episode' in s:
                print("Script snippet:", s[:300])
except Exception as e:
    print('Error:', e)
