import sys
from faster_whisper import WhisperModel

sys.stdout.reconfigure(encoding='utf-8')
model = WhisperModel("base", device="cpu", compute_type="int8")

print("=== Test 6: vad_filter=False with word_timestamps=True ===")
segments, info = model.transcribe(
    "scratch/sample_voc.wav",
    language="zh",
    vad_filter=False,
    word_timestamps=True
)
for s in segments:
    print(f"[{s.start:.2f}-{s.end:.2f}] {s.text}")
    for w in s.words:
        print(f"    [{w.start:.2f}-{w.end:.2f}] {w.word}")
