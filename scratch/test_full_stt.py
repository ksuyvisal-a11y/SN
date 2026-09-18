import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding='utf-8')

from stt_engine import SpeechToTextEngine

eng = SpeechToTextEngine('base')
print("Transcribing full 3-minute audio...")
res = eng.transcribe_audio("data/projects/5bce584c/original_audio_vocals.wav", source_lang="zh")
print(f"\n=======================================================")
print(f"Total dialogues found in 3-minute audio: {len(res)} (Previous was 61)")
print(f"First dialogue: [{res[0]['start']}s - {res[0]['end']}s] ({res[0]['speaker']}) {res[0]['text']}")
print(f"Last dialogue:  [{res[-1]['start']}s - {res[-1]['end']}s] ({res[-1]['speaker']}) {res[-1]['text']}")
print(f"=======================================================\n")

# Check dialogues in the formerly blank region (120s - 165s)
print("Dialogues in formerly blank region (120s - 165s):")
in_region = [d for d in res if 120 <= d['start'] <= 165 or 120 <= d['end'] <= 165]
print(f"Found {len(in_region)} lines in this region (Previously only 4 lines):")
for d in in_region:
    print(f"  [{d['start']:06.2f} - {d['end']:06.2f}] ({d['speaker']}) {d['text']}")
