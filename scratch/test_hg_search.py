import sys
sys.stdout.reconfigure(encoding='utf-8')
import urllib.request
import urllib.parse
import json
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://hongguoduanju.com/',
    'Origin': 'https://hongguoduanju.com'
}

# Test searching for a title on hongguoduanju.com
def test_search(title):
    print(f"Testing search for: {title}")
    encoded = urllib.parse.quote(title)
    urls = [
        f"https://hongguoduanju.com/search?keyword={encoded}",
        f"https://hongguoduanju.com/api/search?keyword={encoded}",
        f"https://hongguoduanju.com/search?query={encoded}"
    ]
    for u in urls:
        try:
            req = urllib.request.Request(u, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as res:
                print(f"URL: {u} -> Status {res.status}")
                html = res.read().decode('utf-8', errors='ignore')
                print(f"Length: {len(html)}")
                # check for series_id or player links
                sids = re.findall(r'series_id=(\d+)', html)
                player_links = re.findall(r'/player/(\d+)/(\d+)', html)
                detail_links = re.findall(r'/detail\?series_id=(\d+)', html)
                print(f"sids: {sids[:5]}, player_links: {player_links[:5]}, detail_links: {detail_links[:5]}")
        except Exception as e:
            print(f"Failed {u}: {e}")

test_search("东北话事人")
test_search("严禄")
