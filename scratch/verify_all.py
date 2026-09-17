import sys
import asyncio
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from stt_engine import SpeechToTextEngine
from translator import DramaTranslator

async def main():
    print("Testing upgraded STT Engine & Drama Translator...")
    stt = SpeechToTextEngine(model_size="base")
    translator = DramaTranslator()

    audio_path = "data/projects/4b45396e/original_audio.wav"
    print(f"Transcribing audio snippet with acoustic pitch and consolidation: {audio_path}")
    
    # Transcribe
    dialogues = stt.transcribe_audio(audio_path=audio_path, source_lang="zh")
    print(f"Total consolidated dialogue lines: {len(dialogues)}")
    
    # Translate first 10
    sample_dialogues = dialogues[:10]
    translated = await translator.translate_dialogues(sample_dialogues, mode="drama_dubbing", source_lang="zh")
    
    with open("scratch_verify_output.txt", "w", encoding="utf-8") as out:
        for item in translated:
            dur = round(item["end"] - item["start"], 2)
            out.write(f"[{item['id']:2d}] {item['start']:5.2f}s -> {item['end']:5.2f}s ({dur:4.2f}s) | {item['speaker']} ({item['voice']})\n")
            out.write(f"   ZH: {item['text_original']}\n")
            out.write(f"   KM: {item['text_km']}\n\n")

    print("Successfully verified! Results written to scratch_verify_output.txt")

if __name__ == "__main__":
    asyncio.run(main())
