import sys
from pathlib import Path

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent.parent))

import hongguo_service

print("Hongguo installed:", hongguo_service.is_installed())
print("Signer online:", hongguo_service.is_signer_online())

# Test fetching episodes for 东北话事人 (7683196130645003288)
sid = "7683196130645003288"
data = hongguo_service.fetch_series_episodes(sid)
print(f"fetch_series_episodes returned: total={data.get('total') if data else 'None'}, episodes={len(data.get('episodes', [])) if data else 0}")
