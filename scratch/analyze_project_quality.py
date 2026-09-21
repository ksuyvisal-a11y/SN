import json
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

with open("data/projects/84995c0c.json", "r", encoding="utf-8") as f:
    project = json.load(f)

dialogues = project.get("dialogues", [])
print(f"Total Dialogues: {len(dialogues)}")
print(f"Project Voice Setting in Config: {project.get('mode')}")
print("=" * 80)

voices_count = {}
robot_words = ["អ្នក", "មនុស្សរបស់អ្នក", "ប្រជាជនរបស់ខ្ញុំ"]
issues = []

for idx, d in enumerate(dialogues):
    spk = d.get("speaker", "unknown")
    v = d.get("voice", "unknown")
    voices_count[v] = voices_count.get(v, 0) + 1
    
    zh = d.get("text_original", "")
    km = d.get("text_km", "")
    start = d.get("start", 0)
    end = d.get("end", 0)
    dur = round(end - start, 2)
    
    # Check mechanical pronouns
    robotic = [w for w in ["អ្នក", "ពួកគេ", "នាង"] if w in km]
    
    print(f"[{idx+1:03d}] {start}s -> {end}s ({dur}s) | Voice: {v} | Speaker: {spk}")
    print(f"   ZH: {zh}")
    print(f"   KM: {km}")
    
    # Analyze issues
    if len(km) > 0 and len(km.split()) > 15 and dur < 2.0:
        print(f"   ⚠️ WARNING: Too much Khmer text for short duration ({len(km.split())} words in {dur}s)")
    if any(ch in zh for ch in ["她", "妈", "姐", "妹", "小姐", "夫人", "婆婆"]) and v == "piseth":
        print(f"   ⚠️ SUSPICIOUS: Female keyword in Chinese text but voiced by Male (piseth)")
    if km == zh:
        print(f"   ⚠️ UNTRANSLATED: Khmer text identical to Chinese")
    print("-" * 80)

print("\nVOICE DISTRIBUTION:")
for k, val in voices_count.items():
    print(f"  {k}: {val} lines ({val/len(dialogues)*100:.1f}%)")
