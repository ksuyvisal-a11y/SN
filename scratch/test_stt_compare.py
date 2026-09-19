import sys
from faster_whisper import WhisperModel

sys.stdout.reconfigure(encoding='utf-8')
model = WhisperModel("base", device="cpu", compute_type="int8")

print("--- Test 1: Vocals wav with current VAD (120-170s) ---")
segments, info = model.transcribe(
    "data/projects/5bce584c/original_audio_vocals.wav",
    language="zh",
    vad_filter=True,
    vad_parameters=dict(threshold=0.32, min_speech_duration_ms=100, max_speech_duration_s=12.0, min_silence_duration_ms=350, speech_pad_ms=180)
)
for s in segments:
    if 120 <= s.start <= 170 or 120 <= s.end <= 170:
        print(f"[{s.start:.2f}-{s.end:.2f}] {s.text}")

print("\n--- Test 2: Vocals wav with vad_filter=False (120-170s) ---")
segments, info = model.transcribe(
    "data/projects/5bce584c/original_audio_vocals.wav",
    language="zh",
    vad_filter=False
)
for s in segments:
    if 120 <= s.start <= 170 or 120 <= s.end <= 170:
        print(f"[{s.start:.2f}-{s.end:.2f}] {s.text}")

print("\n--- Test 3: Original wav with vad_filter=False (120-170s) ---")
segments, info = model.transcribe(
    "data/projects/5bce584c/original_audio.wav",
    language="zh",
    vad_filter=False
)
for s in segments:
    if 120 <= s.start <= 170 or 120 <= s.end <= 170:
        print(f"[{s.start:.2f}-{s.end:.2f}] {s.text}")
