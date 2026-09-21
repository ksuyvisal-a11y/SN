import json
from pathlib import Path

p_file = Path("data/projects/2acd4b0b.json")
with open(p_file, "r", encoding="utf-8") as f:
    p = json.load(f)

dialogues = p.get("dialogues", [])
print(f"Total dialogues: {len(dialogues)}")

speech_intervals = []
for d in dialogues:
    start_ms = int(d.get("start", 0) * 1000)
    # audio file length
    dur = d.get("audio_duration", d.get("end", 0) - d.get("start", 0))
    speech_end_ms = start_ms + int(dur * 1000)
    
    orig_start_ms = max(0, int(d.get("start", 0) * 1000))
    orig_end_ms = max(0, int(d.get("end", 0) * 1000))

    pad_start = max(0, min(orig_start_ms, start_ms) - 160)
    pad_end = max(orig_end_ms, speech_end_ms) + 180
    speech_intervals.append((pad_start, pad_end))

speech_intervals.sort(key=lambda x: x[0])
merged = []
for s, e in speech_intervals:
    if not merged:
        merged.append([s, e])
    else:
        if s <= merged[-1][1] + 1800:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])

print(f"Merged intervals: {len(merged)}")
for idx, (s, e) in enumerate(merged[:15]):
    print(f"Interval {idx+1}: {s/1000.0:.2f}s -> {e/1000.0:.2f}s (dur={(e-s)/1000.0:.2f}s)")
    if idx > 0:
        gap = (s - merged[idx-1][1]) / 1000.0
        print(f"   [Gap / BGM jump back to 1.0: {gap:.2f}s]")
