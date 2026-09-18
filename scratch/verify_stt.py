import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding='utf-8')
from stt_engine import SpeechToTextEngine

eng = SpeechToTextEngine('base')
res = eng.transcribe_audio('scratch/sample_voc.wav', 'zh')
print(f"Total dialogues found in 45s: {len(res)}")
for d in res:
    print(f"#{d['id']:02d} [{d['start']:05.2f}-{d['end']:05.2f}] ({d['speaker']}) {d['text']}")
