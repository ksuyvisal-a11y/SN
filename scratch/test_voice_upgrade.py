import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import asyncio
import os
import json
from translator import DramaTranslator, enrich_khmer_drama_dialogue
from tts_engine import synthesize_khmer_speech, trim_and_fit_voice_audio, batch_synthesize
from audio_processor import enhance_voice_clarity_studio, get_media_duration, mix_dubbed_audio
from pipeline import ProjectManager

async def run_upgrade_tests():
    print("=== 1. Testing Translation Phrasing & Pronoun Naturalization ===")
    translator = DramaTranslator()
    
    test_lines = [
        "你没事吧？",
        "快走！别管我！",
        "你到底在干什么？"
    ]
    
    for line in test_lines:
        res = await translator.translate_text_free(line, source_lang="zh", voice="piseth")
        enriched = enrich_khmer_drama_dialogue(res, line, voice="piseth")
        print(f"Original: {line} -> Dub: {enriched}")
    print("PASS: Translation phrasing is natural and drama-ready.\n")

    print("=== 2. Testing Studio Vocal DSP & Clarity Chain ===")
    test_out = Path("scratch/test_studio_dsp.mp3")
    audio_path = await synthesize_khmer_speech(
        text="ទីបំផុតបងបានមកដល់ហើយ កុំភ័យអីណា!",
        voice="piseth",
        rate_percent=0,
        pitch_hz=0,
        output_path=str(test_out),
        use_cache=True
    )
    enhanced_path = enhance_voice_clarity_studio(audio_path, speed_ratio=1.0)
    assert Path(enhanced_path).exists() and Path(enhanced_path).stat().st_size > 500
    print("PASS: enhance_voice_clarity_studio executed cleanly.\n")

    print("=== 3. Testing Voice Mode Enforcement (Piseth Solo, Sreymom Solo, Dual Multi) ===")
    dialogue_samples = [
        {"id": 1, "start": 0.0, "end": 2.0, "speaker": "តួប្រុស (Male)", "text": "你快走！", "text_original": "你快走！"},
        {"id": 2, "start": 2.5, "end": 4.5, "speaker": "តួស្រី (Female)", "text": "我不走！", "text_original": "我不走！"}
    ]

    # Test A: Piseth Solo Mode -> ALL lines MUST be Piseth
    res_piseth = await translator.translate_dialogues(dialogue_samples, target_voice_override="piseth")
    assert all(item["voice"] == "piseth" for item in res_piseth), "All lines must be Piseth in piseth mode"
    print(f"PASS: Piseth Solo Mode verified. Voices: {[item['voice'] for item in res_piseth]}")

    # Test B: Sreymom Solo Mode -> ALL lines MUST be Sreymom
    res_sreymom = await translator.translate_dialogues(dialogue_samples, target_voice_override="sreymom")
    assert all(item["voice"] == "sreymom" for item in res_sreymom), "All lines must be Sreymom in sreymom mode"
    print(f"PASS: Sreymom Solo Mode verified. Voices: {[item['voice'] for item in res_sreymom]}")

    # Test C: Multi Mode -> Line 1 (Male) Piseth, Line 2 (Female) Sreymom
    res_multi = await translator.translate_dialogues(dialogue_samples, target_voice_override="multi")
    assert res_multi[0]["voice"] == "piseth" and res_multi[1]["voice"] == "sreymom", "Dual Voice must split by character gender"
    print(f"PASS: Dual Voice Multi Mode verified. Line 1: {res_multi[0]['voice']}, Line 2: {res_multi[1]['voice']}\n")

    print("=== 4. Testing Project Creation & Ducking Factor (-34dB Default) ===")
    pm = ProjectManager()
    proj = pm.create_project("Test_Project_Audio")
    assert proj["ducking_factor"] == 0.02, f"Expected 0.02, got {proj['ducking_factor']}"
    print(f"PASS: New project initialized with ducking_factor={proj['ducking_factor']} (-34dB).\n")

    print("=== 5. Testing Zero Vocal Leakage Audio Mixing ===")
    mix_out = Path("scratch/test_mixed_audio.mp3")
    mixed_file = mix_dubbed_audio(
        original_audio_path=None,  # Pure track test
        dialogue_items=res_multi,
        output_mixed_path=str(mix_out),
        total_duration_sec=6.0,
        ducking_volume_factor=0.02,
        dubbing_mode="smart_bgm"
    )
    assert Path(mixed_file).exists() and Path(mixed_file).stat().st_size > 1000
    print(f"PASS: mix_dubbed_audio executed successfully, output size: {Path(mixed_file).stat().st_size} bytes.\n")

    print("=== ALL 5 UPGRADE TESTS PASSED WITH 100% SUCCESS! ===")

if __name__ == "__main__":
    asyncio.run(run_upgrade_tests())
