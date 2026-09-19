import sys
import json
import asyncio
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent.parent))

from server import load_stored_story_config
from translator import resolve_dubbing_mode, DramaTranslator
from tts_engine import synthesize_khmer_speech

async def full_check():
    cfg = load_stored_story_config()
    print("1. Story config:", cfg.get('khmer_voice'), "auto_multi:", cfg.get('auto_multi_voice'))
    assert cfg.get('khmer_voice') == 'piseth', "Config khmer_voice must be piseth"
    assert cfg.get('auto_multi_voice') is False, "Config auto_multi_voice must be False"

    is_multi, chosen = resolve_dubbing_mode()
    print("2. Dubbing mode:", is_multi, "Chosen voice:", chosen)
    assert is_multi is False, "Dubbing mode must be False (Single Voice)"
    assert chosen == 'piseth', "Chosen voice must be piseth"

    t = DramaTranslator()
    test_dialogues = [
        {'id': 1, 'start': 0.0, 'end': 3.0, 'text': '林早早，你看你脸上写着白痴两个字！', 'text_original': '林早早，你看你脸上写着白痴两个字！'},
        {'id': 2, 'start': 3.0, 'end': 6.0, 'text': '李沐谦，你肚子里的孩子到底是谁的？', 'text_original': '李沐谦，你肚子里的孩子到底是谁的？'},
        {'id': 3, 'start': 6.0, 'end': 9.0, 'text': '沈曼琳，你不要给脸不要脸！', 'text_original': '沈曼琳，你不要给脸不要脸！'},
        {'id': 4, 'start': 9.0, 'end': 12.0, 'text': '婆婆，求求你放过我吧！', 'text_original': '婆婆，求求你放过我吧！'},
        {'id': 5, 'start': 12.0, 'end': 15.0, 'text': '混蛋，你给我滚出去！', 'text_original': '混蛋，你给我滚出去！'}
    ]

    print("3. Translating test drama lines...")
    res = await t.translate_dialogues(test_dialogues)
    print(f"Translated {len(res)} items:")
    for idx, item in enumerate(res):
        v = item.get('voice')
        p = item.get('pitch_hz')
        r = item.get('rate_percent')
        s = item.get('speaker')
        t_km = item.get('text_km')
        print(f"  Line {idx+1}: [{v}] (Pitch={p}Hz, Rate={r}%) | Speaker: {s} | KM: {t_km}")
        assert v == 'piseth', f"Line {idx+1} voice must be piseth, got {v}"
        assert p == 0, f"Line {idx+1} pitch must be 0, got {p}"
        assert r == 0, f"Line {idx+1} rate must be 0, got {r}"
        assert s == 'ពិសិដ្ឋ (Piseth Solo)', f"Line {idx+1} speaker must be ពិសិដ្ឋ (Piseth Solo), got {s}"

    print("4. Testing single-breath speech synthesis...")
    audio_f = await synthesize_khmer_speech(res[0]['text_km'], voice=res[0]['voice'], rate_percent=res[0]['rate_percent'], pitch_hz=res[0]['pitch_hz'])
    print("  TTS Synthesized audio file:", audio_f)
    assert Path(audio_f).exists() and Path(audio_f).stat().st_size > 500, "Synthesized audio file must exist and be valid"

    print("\n✅ ALL SINGLE VOICE VERIFICATIONS PASSED 100%!")

if __name__ == "__main__":
    asyncio.run(full_check())
