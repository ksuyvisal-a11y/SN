import urllib.request
import json
from pathlib import Path

raw_new_keys = """
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
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
"""

new_keys = [k.strip() for k in raw_new_keys.strip().splitlines() if k.strip()]
print(f"Total new keys to check: {len(new_keys)}")

valid_new = []
invalid_new = []

for i, k in enumerate(new_keys, 1):
    req = urllib.request.Request('https://api.groq.com/openai/v1/models', headers={'Authorization': f'Bearer {k}', 'User-Agent': 'Python/3.10'})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                valid_new.append(k)
                print(f"[{i}/{len(new_keys)}] {k[:14]}... OK")
    except Exception as e:
        invalid_new.append((k, str(e)))
        print(f"[{i}/{len(new_keys)}] {k[:14]}... FAILED: {e}")

print(f"\nValid new keys: {len(valid_new)} / {len(new_keys)}")

# Load existing config
cfg_file = Path("data/ai_provider_config.json")
with open(cfg_file, "r", encoding="utf-8") as f:
    cfg = json.load(f)

existing_keys = cfg.get("groq_keys", [])
merged = []
seen = set()

# Preserve existing keys order first
for k in existing_keys:
    if k not in seen:
        seen.add(k)
        merged.append(k)

# Add new valid keys
for k in valid_new:
    if k not in seen:
        seen.add(k)
        merged.append(k)

cfg["groq_keys"] = merged
if not cfg.get("groq_api_key") and merged:
    cfg["groq_api_key"] = merged[0]

with open(cfg_file, "w", encoding="utf-8") as f:
    json.dump(cfg, f, ensure_ascii=False, indent=2)

print(f"Successfully merged keys! Total keys in pool: {len(merged)}")
