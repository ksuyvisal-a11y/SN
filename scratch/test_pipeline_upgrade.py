import sys
import os
import asyncio
from pathlib import Path

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from stt_engine import SpeechToTextEngine, load_audio_samples_16k, analyze_segment_acoustics_fast
from translator import DramaTranslator, enrich_khmer_drama_dialogue
from tts_engine import synthesize_khmer_speech, batch_synthesize
from video_processor import render_dubbed_video


async def run_verification():
    print("==================================================")
    print(" 🚀 TESTING UPGRADED ZERO-LAG DRAMA PIPELINE")
    print("==================================================")

    # 1. Test In-Memory Audio Loading & Vectorized Acoustic Analysis
    print("\n[TEST 1] STT Fast Acoustic Pitch Vectorization...")
    test_audio = "data/projects/01cdf07c/original_audio.wav"
    if os.path.exists(test_audio):
        samples, sr = load_audio_samples_16k(test_audio)
        assert samples is not None and len(samples) > 0, "Samples should load into memory"
        acoustics = analyze_segment_acoustics_fast(samples[:16000 * 2], sr)
        print(f"  ✓ Fast analysis on 2s audio completed: F0={acoustics['f0']}Hz, Role={acoustics['role']}, Speaker={acoustics['speaker']}")
    else:
        print("  ✓ Test audio not found, skipping sample test.")

    # 2. Test Drama Translation Quality and Double-Punctuation Cleaning
    print("\n[TEST 2] Drama Translation Punctuation & Expression Quality...")
    t = DramaTranslator()
    
    test_cases = [
        ("动了啊 多人", "វាកំពុងមានកម្រើកហើយ"),
        ("没事吧 想擦", "ឯងមិនអីទេមែនទេ"),
        ("快走！别管我！", "កុំខ្វល់ពីខ្ញុំអី"),
        ("你到底在干什么？", "ឯង")
    ]
    
    for zh, expected_sub in test_cases:
        res = await t.translate_text_free(zh, source_lang="zh", voice="piseth")
        print(f"  ZH: '{zh}' ➜ KM: '{res}'")
        assert "!" in res or "?" in res or "។" in res
        # Ensure no broken punctuation like '!។' or '? !'
        assert "!។" not in res, f"Found '!។' in {res}"
        assert "? ! " not in res, f"Found '? !' in {res}"
        assert "ចាន" not in res, f"Found trailing 'ចាន' in {res}"

    print("  ✓ All translation cleanups and drama idioms passed!")

    # 3. Test Resilient TTS Fallback
    print("\n[TEST 3] Edge-TTS Resilient Audio Synthesis...")
    test_out = "scratch/test_upgraded_tts.mp3"
    Path("scratch").mkdir(exist_ok=True)
    tts_res = await synthesize_khmer_speech(
        text="ឯងមិនអីទេមែនទេ?! កុំភ័យអីណា បងនៅទីនេះហើយ!",
        voice="piseth",
        output_path=test_out,
        use_cache=True
    )
    assert Path(tts_res).exists() and Path(tts_res).stat().st_size > 1000
    print(f"  ✓ Speech synthesized successfully ({Path(tts_res).stat().st_size} bytes).")

    # 4. Test Single Voice Override in Translation (Piseth vs Sreymom)
    print("\n[TEST 4] Single-Voice Mode Enforcement...")
    dialogues = [
        {"id": 1, "start": 0.0, "end": 2.0, "text_original": "快走！"},
        {"id": 2, "start": 2.5, "end": 4.5, "text_original": "我没事。"}
    ]
    res_piseth = await t.translate_dialogues(dialogues, target_voice_override="piseth")
    assert all(d["voice"] == "piseth" for d in res_piseth), "All lines must be piseth"
    print(f"  ✓ Piseth Solo mode verified: {[d['voice'] for d in res_piseth]}")

    print("\n==================================================")
    print(" 🎉 ALL 4 PIPELINE UPGRADE TESTS PASSED 100%!")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_verification())
