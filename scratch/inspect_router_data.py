import sys
sys.stdout.reconfigure(encoding='utf-8')
import urllib.request
import re
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://hongguoduanju.com/',
    'Origin': 'https://hongguoduanju.com'
}

sid = '7683196130645003288'
url = f"https://hongguoduanju.com/detail?series_id={sid}"

req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=10) as res:
    html = res.read().decode('utf-8', errors='ignore')

m = re.search(r'_ROUTER_DATA\s*=\s*(\{.*?\});', html)
if m:
    data = json.loads(m.group(1))
    loader = data.get("loaderData", {})
    dp = loader.get("detail_page", {})
    print("detail_page keys:", list(dp.keys()))
    for k, v in dp.items():
        if isinstance(v, dict):
            print(f"  {k} keys:", list(v.keys()))
        elif isinstance(v, list):
            print(f"  {k} len:", len(v))
        else:
            print(f"  {k}:", str(v)[:100])
            
    # Check if there is an episode list or video list
    series_info = dp.get("series_info") or dp.get("seriesInfo") or dp.get("data") or {}
    print("\nSeries Info keys:", list(series_info.keys()) if isinstance(series_info, dict) else type(series_info))
    
    # Save the json structure for easy inspection
    with open("scratch/detail_page_sample.json", "w", encoding="utf-8") as f:
        json.dump(dp, f, ensure_ascii=False, indent=2)
    print("\nSaved scratch/detail_page_sample.json")
