import sys
from faster_whisper import WhisperModel

sys.stdout.reconfigure(encoding='utf-8')
model = WhisperModel("base", device="cpu", compute_type="int8")

segments_gen, info = model.transcribe(
    "scratch/sample_voc.wav",
    language="zh",
    beam_size=4,
    vad_filter=False,
    word_timestamps=True,
    condition_on_previous_text=False,
    initial_prompt="以下是普通话短剧影视对白，包含现代职场、家庭情感与对话标点符号："
)

count = 0
for s in segments_gen:
    text = s.text.strip()
    if not text:
        continue
    w_start = round(s.words[0].start, 2) if s.words else round(s.start, 2)
    w_end = round(s.words[-1].end, 2) if s.words else round(s.end, 2)
    count += 1
    print(f"#{count:02d} [{w_start:05.2f}-{w_end:05.2f}] (dur: {w_end-w_start:04.2f}s) {text}")
