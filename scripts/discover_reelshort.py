import urllib.request
import re
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

url = 'https://www.reelshort.com/'
with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as r:
    html = r.read().decode('utf-8', errors='ignore')

m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
d = json.loads(m.group(1))
build_id = d.get('buildId')
print("Build ID:", build_id)

for f in ['_buildManifest.js', '_ssgManifest.js']:
    manifest_url = f'https://www.reelshort.com/_next/static/{build_id}/{f}'
    try:
        with urllib.request.urlopen(urllib.request.Request(manifest_url, headers=headers)) as r2:
            content = r2.read().decode('utf-8', errors='ignore')
            print(f"\n=== {f} ({len(content)} bytes) ===")
            print(content[:1500])
    except Exception as e:
        print(f"{f}: {e}")

# Check all JS bundle files mentioned in html to find all API endpoints
chunks = re.findall(r'src=["\']([^"\']*chunks[^"\']*\.js)["\']', html)
print(f"\nTotal chunk files found in homepage: {len(chunks)}")
api_endpoints = set()

for chunk_path in chunks[:10]:
    c_url = f"https://www.reelshort.com{chunk_path}" if chunk_path.startswith('/') else chunk_path
    try:
        with urllib.request.urlopen(urllib.request.Request(c_url, headers=headers), timeout=10) as cr:
            code = cr.read().decode('utf-8', errors='ignore')
            # Look for /api/ patterns
            apis = re.findall(r'["\'](/api/[a-zA-Z0-9_/-]+)["\']', code)
            for a in apis:
                api_endpoints.add(a)
    except Exception as e:
        pass

print("\n--- Discovered API endpoints in JS chunks ---")
for a in sorted(api_endpoints):
    print(" ", a)
