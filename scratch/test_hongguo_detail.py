import sys
sys.stdout.reconfigure(encoding='utf-8')
import urllib.request
import re
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://hongguoduanju.com/',
    'Origin': 'https://hongguoduanju.com',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
}

test_sids = [
    ('7685224734895655960', '糯糯下山'),
    ('7683196130645003288', '东北话事人'),
    ('7679018384272395289', '全家把我当乡下老太'),
    ('7686433880127048728', 'From Homepage 1'),
]

for sid, name in test_sids:
    url = f"https://hongguoduanju.com/detail?series_id={sid}"
    print(f"\nChecking [{name}] {url} ...", flush=True)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as res:
            html = res.read().decode('utf-8', errors='ignore')
            print(f"  Status: {res.status}, Length: {len(html)}", flush=True)
            
            # Check for title
            tit_m = re.search(r'<title>(.*?)</title>', html)
            print("  Title:", tit_m.group(1) if tit_m else "No title", flush=True)
            
            # Look for player links or video IDs
            player_links = re.findall(r'/player/' + sid + r'/(\d+)', html)
            print(f"  Found /player/{sid}/... count: {len(player_links)}", flush=True)
            if player_links:
                print(f"  First 3 vids: {player_links[:3]}", flush=True)
                
            # Check for _ROUTER_DATA or initial data
            router_m = re.search(r'_ROUTER_DATA\s*=\s*(\{.*?\});', html)
            if router_m:
                print("  _ROUTER_DATA found!", flush=True)
                rd = json.loads(router_m.group(1))
                print("  Loader keys:", list(rd.get("loaderData", {}).keys()), flush=True)
            else:
                # Look for other JSON data in script tags
                script_blocks = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
                for s in script_blocks:
                    if 'series_id' in s or 'video_id' in s or 'player' in s:
                        print("  Found relevant script tag: len", len(s), flush=True)
                        m_var = re.findall(r'window\.(\w+)\s*=\s*({.*?});', s)
                        for vn, val in m_var[:3]:
                            print("    window." + vn + " len:", len(val), flush=True)
    except Exception as e:
        print(f"  ERROR: {e}", flush=True)
