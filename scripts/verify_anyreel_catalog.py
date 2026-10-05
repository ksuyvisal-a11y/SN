import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import downloader
import hongguo_db

print('--- SUPPORTED PLATFORMS ---')
for p in downloader.get_supported_platforms_with_counts():
    cnt = p.get('count', 0)
    print(f" - {p['id']}: {p['name']} -> {cnt:,} dramas | logo: {p.get('logo')}")

print('\n--- ANYREEL DRAMAS SCRAPED FROM anyreel.app (First 5) ---')
dramas, total = hongguo_db.query_dramas(platform='anyreel', limit=5)
print(f"Total AnyReel in DB: {total:,}")
for d in dramas:
    print(f"[{d['id']}] {d['title']}")
    print(f"  Poster: {d['poster']}")
    print(f"  Eps: {d['total_episodes']}, Rating: {d['rating']}, Heat: {d['heat']}")

print('\n--- TESTING DIRECT ANYREEL URL ANALYZE ---')
test_url = 'https://www.anyreel.app/movie/screwing-my-bestie-s-hot-dad-6186'
res = downloader.drama_downloader.analyze_url(test_url)
print('Analyze success:', res.get('success'))
matched_title = res.get('title') or (res.get('drama') or {}).get('title')
print('Matched title:', matched_title)
eps = res.get('episodes', [])
print('Episodes generated:', len(eps))
if eps:
    ep1 = eps[0]
    print('Ep 1 stream resolution:', ep1.get('resolution'))
    print('Ep 1 has valid stream/download URL:', bool(ep1.get('stream_url') or ep1.get('download_url')))
