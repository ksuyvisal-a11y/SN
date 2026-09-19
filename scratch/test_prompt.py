import sys
from faster_whisper import WhisperModel

sys.stdout.reconfigure(encoding='utf-8')
model = WhisperModel("base", device="cpu", compute_type="int8")

print("=== Test 5: vad_filter=False with initial_prompt ===")
segments, info = model.transcribe(
    "scratch/sample_voc.wav",
    language="zh",
    vad_filter=False,
    initial_prompt="以下是普通话短剧对白，总裁、夫人、助理、母亲、儿子、职场、家庭情感剧，包含标点符号："
)
for s in segments:
    print(f"[{s.start:.2f}-{s.end:.2f}] {s.text}")
