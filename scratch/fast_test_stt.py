import sys
from faster_whisper import WhisperModel

sys.stdout.reconfigure(encoding='utf-8')
model = WhisperModel("base", device="cpu", compute_type="int8")

print("=== 1. sample_voc.wav with VAD (Current Engine Setting) ===")
segments, info = model.transcribe(
    "scratch/sample_voc.wav",
    language="zh",
    vad_filter=True,
    vad_parameters=dict(threshold=0.32, min_speech_duration_ms=100, max_speech_duration_s=12.0, min_silence_duration_ms=350, speech_pad_ms=180)
)
for s in segments:
    print(f"[{s.start:.2f}-{s.end:.2f}] {s.text}")

print("\n=== 2. sample_orig.wav with VAD ===")
segments, info = model.transcribe(
    "scratch/sample_orig.wav",
    language="zh",
    vad_filter=True,
    vad_parameters=dict(threshold=0.32, min_speech_duration_ms=100, max_speech_duration_s=12.0, min_silence_duration_ms=350, speech_pad_ms=180)
)
for s in segments:
    print(f"[{s.start:.2f}-{s.end:.2f}] {s.text}")

print("\n=== 3. sample_orig.wav with vad_filter=False ===")
segments, info = model.transcribe(
    "scratch/sample_orig.wav",
    language="zh",
    vad_filter=False
)
for s in segments:
    print(f"[{s.start:.2f}-{s.end:.2f}] {s.text}")

print("\n=== 4. sample_voc.wav with vad_filter=False ===")
segments, info = model.transcribe(
    "scratch/sample_voc.wav",
    language="zh",
    vad_filter=False
)
for s in segments:
    print(f"[{s.start:.2f}-{s.end:.2f}] {s.text}")
