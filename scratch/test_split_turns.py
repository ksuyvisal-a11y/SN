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
    condition_on_previous_text=False
)

raw_segments = []
for s in segments_gen:
    if not s.words:
        text = s.text.strip()
        if text:
            raw_segments.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": text})
        continue
    
    current_words = []
    current_start = None
    
    for i, w in enumerate(s.words):
        word_text = w.word.strip()
        if not word_text:
            continue
        if current_start is None:
            current_start = w.start
        current_words.append(w)
        
        # Check if pause after word is >= 0.45s, or sentence punctuation
        is_last = (i == len(s.words) - 1)
        has_pause = False
        if not is_last:
            next_w = s.words[i + 1]
            if next_w.start - w.end >= 0.45:
                has_pause = True
        
        has_punct = any(p in word_text for p in ["。", "！", "？", "!", "?", "；", ";"])
        
        if is_last or has_pause or (has_punct and len(current_words) >= 4):
            seg_text = "".join([cw.word for cw in current_words]).strip()
            seg_start = round(current_start, 2)
            seg_end = round(w.end, 2)
            if seg_text and seg_end > seg_start:
                raw_segments.append({"start": seg_start, "end": seg_end, "text": seg_text})
            current_words = []
            current_start = None

print(f"Total fine segments: {len(raw_segments)}")
for idx, r in enumerate(raw_segments, 1):
    print(f"#{idx:02d} [{r['start']:05.2f} - {r['end']:05.2f}] (dur: {r['end']-r['start']:04.2f}s) {r['text']}")
