import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import asyncio
import json
from translator import DramaTranslator
from server import load_stored_story_config

async def run_tests():
    print("--- 1. Testing Stored Story Config ---")
    cfg = load_stored_story_config()
    print("Loaded config:", cfg)
    assert cfg.get("auto_multi_voice") is False, "auto_multi_voice should be False by default"
    assert cfg.get("khmer_voice") == "piseth", "khmer_voice should be piseth by default"
    print("PASS: Stored story config is Single Voice (Piseth).\n")

    print("--- 2. Testing Single Voice Default (Piseth) ---")
    translator = DramaTranslator()
    sample_dialogues = [
        {"id": 1, "start": 0.0, "end": 3.0, "speaker": "តួប្រុស (Male)", "text": "你好，我是张三。"},
        {"id": 2, "start": 3.5, "end": 6.5, "speaker": "តួស្រី (Female)", "text": "你好，我是李四。"},
        {"id": 3, "start": 7.0, "end": 10.0, "speaker": "តួប្រុស (Male)", "text": "今天天气很好。"}
    ]

    res_piseth = await translator.translate_dialogues(sample_dialogues, target_voice_override=None)
    for idx, item in enumerate(res_piseth):
        print(f"Line {idx+1}: voice={item['voice']}, speaker={item['speaker']}, text={item['text_km']}")
        assert item["voice"] == "piseth", f"Expected voice piseth on line {idx+1}, got {item['voice']}"
    print("PASS: All lines strictly assigned to single voice 'piseth'.\n")

    print("--- 3. Testing Single Voice Override (Sreymom) ---")
    res_sreymom = await translator.translate_dialogues(sample_dialogues, target_voice_override="sreymom")
    for idx, item in enumerate(res_sreymom):
        print(f"Line {idx+1}: voice={item['voice']}, speaker={item['speaker']}, text={item['text_km']}")
        assert item["voice"] == "sreymom", f"Expected voice sreymom on line {idx+1}, got {item['voice']}"
    print("PASS: All lines strictly assigned to single voice 'sreymom'.\n")

    print("--- 4. Testing Multi-Voice Override (auto_multi) ---")
    res_multi = await translator.translate_dialogues(sample_dialogues, target_voice_override="auto_multi")
    voices = [item["voice"] for item in res_multi]
    print("Multi-voice output voices:", voices)
    assert "piseth" in voices and "sreymom" in voices, "Expected both voices when auto_multi is requested"
    print("PASS: Multi-voice still works when explicitly requested.\n")

    print("=== ALL TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    asyncio.run(run_tests())
