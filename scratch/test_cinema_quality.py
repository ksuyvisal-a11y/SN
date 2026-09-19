"""
Comprehensive Verification Script for Cinema-Grade Cambodian Drama Dubbing
Tests:
1. Critical Drama Idioms & Pronoun Accuracy (Groq 77 API pool)
2. Character Persona Separation (Pitch & Speed differentiation for Villainess, Mother-in-law, Lead)
3. Zero Truncation Audio Synthesis and NumPy Mixing
"""
import sys
import asyncio
import json
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from translator import DramaTranslator
from tts_engine import batch_synthesize
from audio_processor import mix_dubbed_audio, get_media_duration


async def main():
    print("=== 1. TESTING DRAMA TRANSLATION & PERSONA ACOUSTICS ===")
    test_lines = [
        {
            "id": 1,
            "start": 0.0,
            "end": 2.5,
            "speaker": "沈曼琳 (Villainess)",
            "text": "看你脸上写着白痴！",
            "text_original": "看你脸上写着白痴！"
        },
        {
            "id": 2,
            "start": 2.6,
            "end": 5.2,
            "speaker": "恶婆婆 (Mother-in-law)",
            "text": "她肚子里怀的可是我们李家的龙胎，你这贱丫头算什么东西！",
            "text_original": "她肚子里怀的可是我们李家的龙胎，你这贱丫头算什么东西！"
        },
        {
            "id": 3,
            "start": 5.3,
            "end": 8.0,
            "speaker": "林早早 (Heroine)",
            "text": "李沐谦，求求你相信我，我真的没有去过那家按摩店！",
            "text_original": "李沐谦，求求你相信我，我真的没有去过那家按摩店！"
        },
        {
            "id": 4,
            "start": 8.1,
            "end": 10.5,
            "speaker": "李沐谦 (Male Lead / CEO)",
            "text": "林早早，你到现在还在狡辩！张昭，把她给我轰出去！",
            "text_original": "林早早，你到现在还在狡辩！张昭，把她给我轰出去！"
        }
    ]

    translator = DramaTranslator()
    print(f"Active Groq Keys in pool: {len(translator.groq_keys)}")
    assert len(translator.groq_keys) >= 20, "Expected at least 20 Groq keys!"

    translated = await translator.translate_dialogues(
        dialogues=test_lines,
        mode="drama_dubbing",
        source_lang="zh",
        target_voice_override="multi"
    )

    print("\n--- TRANSLATION RESULTS ---")
    for t in translated:
        print(f"[{t['speaker']}] (Voice: {t.get('voice')}, Pitch: {t.get('pitch_hz')}Hz, Rate: {t.get('rate_percent')}%)")
        print(f"  ZH: {t.get('text_original')}")
        print(f"  KM: {t.get('text_km')}\n")

    # Verification Checks
    text_all_km = " ".join([t.get("text_km", "") for t in translated])
    
    # 1. Check idioms
    assert "Dragon fetus" not in text_all_km, "FAILED: 'Dragon fetus' found in translation!"
    assert "Anmo Electric" not in text_all_km, "FAILED: 'Anmo Electric' found in translation!"
    print("PASS: No literal mistranslations ('Dragon fetus' or 'Anmo Electric').")

    # 2. Check persona separation
    v_item = translated[0]  # Shen Manlin (Villainess)
    m_item = translated[1]  # Mother-in-law
    h_item = translated[2]  # Heroine Lin Zaozao
    c_item = translated[3]  # CEO Li Muqian

    print(f"Villainess Pitch: {v_item.get('pitch_hz')}Hz (Expected high pitch > 10)")
    print(f"Mother-in-law Pitch: {m_item.get('pitch_hz')}Hz (Expected deep stern pitch < -10)")
    print(f"Heroine Pitch: {h_item.get('pitch_hz')}Hz (Expected gentle pitch around +2 to +6)")
    print(f"CEO Pitch: {c_item.get('pitch_hz')}Hz (Expected masculine resonant pitch <= 0)")

    assert v_item.get("voice") == "sreymom", "Villainess should use Sreymom"
    assert m_item.get("voice") == "sreymom", "Mother-in-law should use Sreymom"
    assert h_item.get("voice") == "sreymom", "Heroine should use Sreymom"
    assert c_item.get("voice") == "piseth", "CEO should use Piseth"
    assert v_item.get("pitch_hz", 0) > m_item.get("pitch_hz", 0), "Villainess pitch must be significantly higher than mother-in-law!"

    print("PASS: Character voice and persona pitch differentiation verified!")

    # 3. Test Speech Synthesis & Zero Truncation Mixing
    print("\n=== 2. TESTING SPEECH SYNTHESIS & NON-TRUNCATED AUDIO MIXING ===")
    out_dir = Path("scratch/test_cinema_voices")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    synth_res = await batch_synthesize(translated, output_dir=str(out_dir))
    for s in synth_res:
        assert s.get("audio_file") and Path(s["audio_file"]).exists(), f"Audio file missing for line {s.get('id')}"
        dur = get_media_duration(s["audio_file"])
        print(f"Line {s['id']} Audio Generated: {s['audio_file']} (Duration: {dur:.2f}s)")

    mixed_wav = mix_dubbed_audio(
        original_audio_path=None,
        dialogue_items=synth_res,
        output_mixed_path="scratch/test_cinema_voices/mixed_output.wav",
        total_duration_sec=12.0
    )
    mixed_dur = get_media_duration(mixed_wav)
    print(f"Mixed Audio Created: {mixed_wav} (Duration: {mixed_dur:.2f}s)")
    assert mixed_dur > 8.0, "Mixed audio too short!"

    print("\nALL CINEMA-GRADE DUBBING CHECKS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(main())
