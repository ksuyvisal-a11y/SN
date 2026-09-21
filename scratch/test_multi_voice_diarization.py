import json
import sys
sys.path.insert(0, ".")
from stt_engine import SpeechToTextEngine

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

stt = SpeechToTextEngine('base')
# Test on the first 60 seconds of the project's audio
res = stt.transcribe_audio('data/projects/84995c0c/original_audio.wav', voice_override='multi')
male = sum(1 for x in res if x['voice'] == 'piseth')
female = sum(1 for x in res if x['voice'] == 'sreymom')
print(f"Total segments: {len(res)}")
print(f"Male (Piseth): {male} ({male/len(res)*100:.1f}%)")
print(f"Female (Sreymom): {female} ({female/len(res)*100:.1f}%)")

print("\nFirst 20 segments with speaker mapping:")
for x in res[:20]:
    print(f"[{x['start']}s -> {x['end']}s] {x['speaker']} ({x['voice']}): {x['text']}")
