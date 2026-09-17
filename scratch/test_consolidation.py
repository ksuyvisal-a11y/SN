import json

with open('data/projects/4b45396e.json', encoding='utf-8') as f:
    d = json.load(f)

dialogues = d.get('dialogues', [])
print(f"Original segments: {len(dialogues)}")

# Simulate smart merging
merged = []
for seg in dialogues:
    if merged:
        prev = merged[-1]
        gap = round(seg['start'] - prev['end'], 2)
        same_voice = (prev.get('voice') == seg.get('voice'))
        comb_dur = round(seg['end'] - prev['start'], 2)
        
        # Merge if same voice and (small gap or short fragment) and total duration reasonable
        is_short_fragment = (seg['end'] - seg['start'] < 1.4) or (len(seg.get('text_original', '')) <= 4)
        prev_is_short = (prev['end'] - prev['start'] < 1.4)
        
        should_merge = same_voice and comb_dur <= 7.5 and (
            gap <= 0.85 or
            (is_short_fragment and gap <= 1.2) or
            (prev_is_short and gap <= 1.0)
        )
        
        if should_merge:
            prev['end'] = seg['end']
            prev['text_original'] = f"{prev.get('text_original', '')} {seg.get('text_original', '')}".strip()
            continue
            
    merged.append(dict(seg))

print(f"Consolidated segments: {len(merged)}")
print("\nSample consolidated lines that were previously fragmented:")
for item in merged:
    dur = round(item['end'] - item['start'], 2)
    zh = item.get('text_original', '')
    if '曹早' in zh or '林柱莉' in zh or '我能不能活' in zh or '我才是老闆' in zh or '沒關係' in zh:
        print(f"[{item['start']:.2f}s -> {item['end']:.2f}s] ({dur}s) [{item.get('voice')}]: {zh.encode('ascii', 'replace').decode('ascii')}")
