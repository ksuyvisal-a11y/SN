import sys
sys.stdout.reconfigure(encoding='utf-8')
import urllib.request
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://hongguoduanju.com/',
    'Origin': 'https://hongguoduanju.com'
}

req = urllib.request.Request('https://hongguoduanju.com/', headers=headers)
try:
    with urllib.request.urlopen(req, timeout=10) as res:
        html = res.read().decode('utf-8', errors='ignore')
        print(f"Status: {res.status}, Length: {len(html)}", flush=True)
        # Find all hrefs
        hrefs = set(re.findall(r'href=[\"\']([^\"\']+)[\"\']', html))
        print("Hrefs found:", [h for h in hrefs if not h.startswith('#')][:25], flush=True)
        
        # Check if there is router data or initial state
        m = re.findall(r'(\d{15,22})', html)
        print("Long numeric IDs found on homepage:", list(set(m))[:10], flush=True)
except Exception as e:
    print(f"Error: {e}", flush=True)
