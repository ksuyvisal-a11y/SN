import urllib.request
import re
import json

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

# 1. Fetch hongguodownloader.com
print("--- Hongguo Downloader Page ---")
try:
    req = urllib.request.Request('https://hongguodownloader.com/', headers=headers)
    with urllib.request.urlopen(req, timeout=10) as res:
        html = res.read().decode('utf-8', errors='ignore')
        print("Page length:", len(html))
        # Look for API endpoints or download buttons
        endpoints = set(re.findall(r'https?://[a-zA-Z0-9\.\-_/]+', html))
        relevant = [e for e in endpoints if any(k in e.lower() for k in ['api', 'download', 'series', 'drama', 'video', 'play'])]
        print("Relevant endpoints on main page:", relevant[:15])
except Exception as e:
    print("Error fetching hongguodownloader:", e)

# 2. Check hongguoduanju.com for series 7361848529321364506 (东北话事人) or others
print("\n--- Hongguo Duanju Official Web ---")
test_sid = "7361848529321364506" # or from db
detail_url = f"https://hongguoduanju.com/detail?series_id={test_sid}"
try:
    req = urllib.request.Request(detail_url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as res:
        html = res.read().decode('utf-8', errors='ignore')
        print(f"Detail page length for {test_sid}:", len(html))
        vids = re.findall(r'/player/' + test_sid + r'/(\d+)', html)
        print("Found vids in detail HTML:", len(vids), vids[:5])
        
        # Check if there is router data
        m = re.search(r'_ROUTER_DATA\s*=\s*(\{.*?\});', html)
        if m:
            print("Found _ROUTER_DATA in detail page!")
            data = json.loads(m.group(1))
            print("Keys:", list(data.keys()))
        else:
            print("No _ROUTER_DATA in detail page")
except Exception as e:
    print("Error fetching hongguoduanju:", e)

# 3. Check player page on hongguoduanju.com
if vids:
    vid1 = vids[0]
    p_url = f"https://hongguoduanju.com/player/{test_sid}/{vid1}"
    print(f"\n--- Checking Player Page: {p_url} ---")
    try:
        req = urllib.request.Request(p_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as res:
            p_html = res.read().decode('utf-8', errors='ignore')
            print("Player page length:", len(p_html))
            m = re.search(r'_ROUTER_DATA\s*=\s*(\{.*?\});', p_html)
            if m:
                print("Found _ROUTER_DATA in player page!")
                p_data = json.loads(m.group(1))
                loader_data = p_data.get("loaderData", {})
                for k in loader_data:
                    print("  loader key:", k)
                    sub = loader_data[k]
                    if isinstance(sub, dict):
                        print("    sub keys:", list(sub.keys()))
                        v_info = sub.get("video_player_info", {})
                        if v_info:
                            print("    main_url:", v_info.get("main_url")[:100] if v_info.get("main_url") else None)
                        # Check vid_list
                        s_detail = sub.get("seriesDetail", {})
                        if s_detail:
                            print("    seriesDetail keys:", list(s_detail.keys()))
                            print("    vid_list len:", len(s_detail.get("vid_list", [])))
            else:
                print("No _ROUTER_DATA in player page")
    except Exception as e:
        print("Error fetching player page:", e)
