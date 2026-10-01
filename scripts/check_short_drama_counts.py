import sys
import urllib.request
import json

sys.stdout.reconfigure(encoding='utf-8')

categories = [
    (58, "短剧大全 (All Short Dramas)"),
    (65, "重生民国"),
    (66, "穿越年代"),
    (67, "现代言情"),
    (68, "反转爽文"),
    (69, "女恋总裁"),
    (70, "闪婚离婚"),
    (71, "都市脑洞"),
    (72, "古装仙侠"),
    (74, "AI漫剧"),
    (40, "国产动漫 (Donghua/Animation)")
]

headers = {'User-Agent': 'Mozilla/5.0'}

for cid, cname in categories:
    url = f"https://bfzyapi.com/api.php/provide/vod/?ac=list&t={cid}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            data = json.loads(res.read().decode('utf-8'))
            print(f"ID {cid:>2} - {cname:<30} | Total Dramas: {data.get('total', 0):>6} | Pages: {data.get('pagecount', 0):>4}")
    except Exception as e:
        print(f"ID {cid} Error:", e)
