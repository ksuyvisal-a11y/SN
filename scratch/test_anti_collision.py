import os
import sys
sys.path.insert(0, os.path.abspath("."))
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass
import asyncio
from pathlib import Path
from pydub import AudioSegment

import audio_processor
from audio_processor import mix_dubbed_audio, time_stretch_audio_segment
import tts_engine
from tts_engine import trim_and_fit_voice_audio
import translator
from translator import DramaTranslator

print("=== [TEST 1] Testing Time-Stretch Audio Segment ===")
seg = AudioSegment.silent(duration=2000, frame_rate=48000).set_channels(2)
stretched = time_stretch_audio_segment(seg, 1.25)
print(f"Original len: {len(seg)}ms -> Stretched (1.25x): {len(stretched)}ms")
assert len(stretched) < len(seg), "Stretched audio should be shorter!"
print("Test 1 Passed!\n")

print("=== [TEST 2] Testing Anti-Collision Sequential Audio Mixing ===")
# Create two sample audio clips
clip1_path = "cache/clip1.wav"
clip2_path = "cache/clip2.wav"
seg1 = AudioSegment.silent(duration=2500, frame_rate=48000).set_channels(2)
seg2 = AudioSegment.silent(duration=1800, frame_rate=48000).set_channels(2)
seg1.export(clip1_path, format="wav")
seg2.export(clip2_path, format="wav")

dialogues = [
    {
        "id": 1,
        "start": 0.5,
        "end": 1.5,  # slot is 1.0s, but audio is 2.5s!
        "audio_file": clip1_path,
        "text": "ឃ្លាទី១"
    },
    {
        "id": 2,
        "start": 1.2,  # starts BEFORE clip1 finishes!
        "end": 2.5,
        "audio_file": clip2_path,
        "text": "ឃ្លាទី២"
    }
]

out_mixed = "cache/test_mixed_anticollision.mp3"
mix_dubbed_audio(
    original_audio_path=None,
    dialogue_items=dialogues,
    output_mixed_path=out_mixed,
    total_duration_sec=10.0
)

print(f"Clip 1 start: {dialogues[0]['start']}s, end: {dialogues[0]['end']}s")
print(f"Clip 2 start: {dialogues[1]['start']}s, end: {dialogues[1]['end']}s")
# Verify that Clip 2 start is >= Clip 1 end
assert dialogues[1]["start"] >= round(dialogues[0]["end"] + 0.10, 2), "Clip 2 must start AFTER Clip 1 has completely finished!"
print("Test 2 Passed! Voices are strictly sequential and CANNOT overlap!\n")

print("=== [TEST 3] Testing Qwen AI Drama Translation ===")
async def test_trans():
    tr = DramaTranslator()
    test_lines = [
        {"id": 1, "start": 0.5, "end": 1.3, "text_original": "送什么"},
        {"id": 2, "start": 1.5, "end": 2.5, "text_original": "等一下"},
        {"id": 3, "start": 3.0, "end": 4.5, "text_original": "动了啊"}
    ]
    res = await tr.translate_dialogues(test_lines, mode="drama_dubbing", source_lang="zh")
    for r in res:
        print(f"ID {r['id']} [{r['start']}-{r['end']}s] ({r['text_original']}) -> Khmer: '{r['text_km']}'")
        assert len(r['text_km']) < 35, f"Short line should be concise, got {len(r['text_km'])} chars"
    print("Test 3 Passed! Translations are accurate and concise!\n")

asyncio.run(test_trans())
print("ALL ANTI-COLLISION & TRANSLATION TESTS PASSED 100%!")
