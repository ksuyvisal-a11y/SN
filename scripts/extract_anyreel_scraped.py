import xml.etree.ElementTree as ET
import json
import re
from pathlib import Path

scraped = []
seen_titles = set()

# 1. Parse video-sitemap
p_video = Path(r'C:\Users\M\.gemini\antigravity-ide\brain\29475635-d246-4137-bc57-4ef6ded9aedb\.system_generated\steps\697\content.md')
if p_video.exists():
    with open(p_video, 'r', encoding='utf-8') as f:
        text = f.read()
    xml_start = text.find('<?xml')
    if xml_start != -1:
        root = ET.fromstring(text[xml_start:])
        for u in root.findall('{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
            v = u.find('{http://www.google.com/schemas/sitemap-video/1.1}video')
            if v is not None:
                t = v.find('{http://www.google.com/schemas/sitemap-video/1.1}title')
                desc = v.find('{http://www.google.com/schemas/sitemap-video/1.1}description')
                thumb = v.find('{http://www.google.com/schemas/sitemap-video/1.1}thumbnail_loc')
                player = v.find('{http://www.google.com/schemas/sitemap-video/1.1}player_loc')
                loc = u.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                
                title_val = t.text.strip() if (t is not None and t.text) else ''
                if title_val and title_val not in seen_titles:
                    seen_titles.add(title_val)
                    scraped.append({
                        'title': title_val,
                        'description': desc.text.strip() if (desc is not None and desc.text) else '',
                        'poster': thumb.text.strip() if (thumb is not None and thumb.text) else '',
                        'player_loc': player.text.strip() if (player is not None and player.text) else '',
                        'page_url': loc.text.strip() if (loc is not None and loc.text) else ''
                    })

# 2. Parse home page json-ld
p_home = Path(r'C:\Users\M\.gemini\antigravity-ide\brain\29475635-d246-4137-bc57-4ef6ded9aedb\.system_generated\steps\677\content.md')
if p_home.exists():
    with open(p_home, 'r', encoding='utf-8') as f:
        h_text = f.read()
    for m in re.finditer(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', h_text, re.DOTALL):
        try:
            data = json.loads(m.group(1))
            for g in data.get('@graph', []):
                for elem in g.get('itemListElement', []):
                    item = elem.get('item', {})
                    t = item.get('name')
                    img = item.get('image')
                    url = item.get('url')
                    if t and t not in seen_titles:
                        seen_titles.add(t)
                        scraped.append({
                            'title': t,
                            'description': '',
                            'poster': img or '',
                            'player_loc': '',
                            'page_url': url or ''
                        })
        except Exception:
            pass

print(f'Total scraped AnyReel official dramas: {len(scraped)}')
with open('data/anyreel_official_scraped.json', 'w', encoding='utf-8') as out:
    json.dump(scraped, out, ensure_ascii=False, indent=2)
print('Saved to data/anyreel_official_scraped.json')
