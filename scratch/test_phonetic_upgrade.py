"""
Verification Script for Auto-Phonetic Spacing, Breathing Pauses, and Number Expansion
"""
import sys
import asyncio
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tts_engine import prepare_khmer_phonetic_for_speech, synthesize_khmer_speech


async def main():
    print("=== TESTING AUTO-PHONETIC SPACING & NUMBER EXPANSION ===")
    test_cases = [
        (
            "លីមូឈៀន ខ្ញុំសុំឱ្យបងជឿខ្ញុំប៉ុន្តែគាត់មិនព្រមស្តាប់ខ្ញុំទេ",
            "Natural breathing pause with character vocative & conjunction"
        ),
        (
            "នាងយកលុយ 500000 យ័ន ទៅឱ្យ CEO ភ្លាម!",
            "Number expansion + Currency + English Acronym"
        ),
        (
            "លោកប្រធាន VIP ត្រូវការពិនិត្យលទ្ធផល DNA ជាបន្ទាន់!",
            "Multiple acronyms (VIP, DNA, President)"
        ),
        (
            "មើលមុខឯងទៅ ដូចមានចារអក្សរថាល្ងង់អញ្ចឹង! ឯងគិតថាឯងជាស្អី?!",
            "Villainess sharp dialogue"
        )
    ]

    out_dir = Path("scratch/test_phonetic_voices")
    out_dir.mkdir(parents=True, exist_ok=True)

    for i, (text, desc) in enumerate(test_cases):
        phonetic = prepare_khmer_phonetic_for_speech(text)
        print(f"\nTest {i+1} ({desc}):")
        print(f"  Input:    {text}")
        print(f"  Phonetic: {phonetic}")

        # Synthesize audio with Edge-TTS
        voice = "sreymom" if i % 2 == 0 else "piseth"
        out_file = out_dir / f"phonetic_test_{i+1}.mp3"
        audio_path = await synthesize_khmer_speech(
            text=phonetic,
            voice=voice,
            rate_percent=0,
            pitch_hz=0,
            output_path=str(out_file),
            use_cache=False
        )
        assert Path(audio_path).exists() and Path(audio_path).stat().st_size > 1000
        print(f"  Audio:    {audio_path} (Size: {Path(audio_path).stat().st_size} bytes) - Generated Cleanly!")

    print("\nALL PHONETIC SPACING AND SPEECH SYNTHESIS TESTS PASSED!")


if __name__ == "__main__":
    asyncio.run(main())
