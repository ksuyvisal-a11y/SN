import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
data = json.load(open('data/projects/5bce584c.json', encoding='utf-8'))
dialogues = data.get('dialogues', [])
print(f"Total lines: {len(dialogues)}")

missing_km = 0
missing_audio = 0
failed_audio = 0

for item in dialogues:
    line_id = item.get("id")
    start = item.get("start")
    end = item.get("end")
    zh = item.get("text_original", "")
    km = item.get("text_km", "")
    dur = item.get("audio_duration", 0)
    succ = item.get("success", False)
    voice = item.get("voice_used", item.get("voice", ""))
    
    if not km:
        missing_km += 1
    if not item.get("audio_file"):
        missing_audio += 1
    if not succ:
        failed_audio += 1
        
    print(f"#{line_id:02d} [{start:06.2f} - {end:06.2f}] ({voice}) ZH: {zh} --> KM: {km} (Audio: {dur:.2f}s, OK: {succ})")

print(f"\nSummary: missing_km={missing_km}, missing_audio={missing_audio}, failed_audio={failed_audio}")
