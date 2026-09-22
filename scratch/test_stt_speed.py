import sys
import time
from pathlib import Path

# Set stdout to UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from stt_engine import SpeechToTextEngine

wav_file = r"D:\Sal\SN\data\projects\01cdf07c\original_audio.wav"
if not Path(wav_file).exists():
    print(f"File not found: {wav_file}")
    sys.exit(0)

print(f"Testing STT with base model on: {wav_file}")
t0 = time.time()
engine = SpeechToTextEngine(model_size="base")
print(f"Model initialized in {time.time() - t0:.2f}s")

t1 = time.time()
segments = engine.transcribe_audio(wav_file, source_lang="auto")
elapsed = time.time() - t1
print(f"Transcription finished in {elapsed:.2f}s! Total segments: {len(segments)}")

for s in segments[:6]:
    print(f"[{s['start']:.2f}s -> {s['end']:.2f}s] ({s['voice']}): {s['text']}")

print("✅ STT Test Succeeded!")
