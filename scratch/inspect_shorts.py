import json

with open('data/projects/4b45396e.json', encoding='utf-8') as f:
    d = json.load(f)

dialogues = d.get('dialogues', [])
print(f"Total dialogues: {len(dialogues)}")

with open('scratch_shorts.txt', 'w', encoding='utf-8') as out:
    for item in dialogues:
        dur = round(item.get('end', 0) - item.get('start', 0), 2)
        km = str(item.get('text_km', '')).strip()
        zh = str(item.get('text_original', '')).strip()
        speaker = item.get('speaker', '')
        voice = item.get('voice', '')
        # If duration < 2.5s or text is short
        if dur < 2.5 or len(km) < 25:
            out.write(f"ID {item['id']} | dur={dur}s | {speaker} ({voice})\n")
            out.write(f"  ZH: {zh}\n")
            out.write(f"  KM: {km}\n\n")

print("Wrote to scratch_shorts.txt")
