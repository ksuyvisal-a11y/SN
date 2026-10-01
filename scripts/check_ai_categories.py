import sys
import urllib.request
import json

sys.stdout.reconfigure(encoding='utf-8')

url = "https://bfzyapi.com/api.php/provide/vod/?ac=list"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=10) as res:
        data = json.loads(res.read().decode('utf-8'))
        print("Total vods across entire source:", data.get('total'))
        print("Page count:", data.get('pagecount'))
        print("\n--- Available Categories ---")
        for c in data.get('class', []):
            print(f"ID: {c.get('type_id'):>3} | Name: {c.get('type_name')} (PID: {c.get('type_pid')})")
except Exception as e:
    print("Error:", e)
