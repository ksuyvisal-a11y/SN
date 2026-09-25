import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath("."))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
from translator import DramaTranslator, enrich_khmer_drama_dialogue

print("--- Testing enrich_khmer_drama_dialogue (No Dropped Words) ---")
# Standalone short shout
t1 = enrich_khmer_drama_dialogue("ឆាប់ទៅ!", "快走！", duration_sec=1.0)
print(f"Standalone shout '快走！' (1.0s): {t1}")

# Full sentence containing '快走' and other words - MUST NOT BE OVERWRITTEN!
t2 = enrich_khmer_drama_dialogue("ឆាប់ទៅពួកយើងនឹងយឺតពេលហើយ!", "快走吧，我们要迟到了！", duration_sec=1.8)
print(f"Full sentence with '快走': {t2}")

# Standalone '等'
t3 = enrich_khmer_drama_dialogue("ចាំសិន!", "等等我", duration_sec=0.9)
print(f"Standalone shout '等等我' (0.9s): {t3}")

# Full sentence containing '等' - MUST NOT BE OVERWRITTEN!
t4 = enrich_khmer_drama_dialogue("ចាំសិន ខ្ញុំមានរឿងសំខាន់ចង់និយាយជាមួយអ្នក!", "等一下，我有重要的话想跟你说！", duration_sec=2.5)
print(f"Full sentence with '等一下': {t4}")

async def test_groq():
    tr = DramaTranslator()
    dialogues = [
        {"id": 1, "start": 0.0, "end": 1.2, "text_original": "快走！", "speaker": "Female"},
        {"id": 2, "start": 1.5, "end": 3.8, "text_original": "快走吧，我们要迟到了！", "speaker": "Female"},
        {"id": 3, "start": 4.2, "end": 6.8, "text_original": "等一下，我有重要的事情要告诉你！", "speaker": "Male"},
        {"id": 4, "start": 7.2, "end": 8.5, "text_original": "闭嘴！我不想听！", "speaker": "Female"}
    ]
    res = await tr.translate_dialogues(dialogues)
    print("\n--- Groq/Qwen Drama Dubbing Translation Output ---")
    for r in res:
        print(f"ID {r['id']} ({r['start']}s -> {r['end']}s, dur={r['end']-r['start']:.1f}s): {r['text_original']} -> '{r['text_km']}' [{r['voice']}]")

    print("\n--- Testing batch_synthesize with Dynamic Tempo Rate ---")
    from tts_engine import batch_synthesize
    tts_results = await batch_synthesize(res, output_dir="cache/test_voice_sync")
    for tr in tts_results:
        orig_slot = tr['orig_end'] - tr['orig_start']
        print(f"Line {tr['id']}: slot={orig_slot:.2f}s | rate={tr['rate_percent']}% | audio_len={tr['audio_duration']:.2f}s | end={tr['end']:.2f}s | audio={tr['audio_file']}")

if __name__ == "__main__":
    asyncio.run(test_groq())
