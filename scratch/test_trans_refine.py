import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from translator import DramaTranslator

async def test():
    tr = DramaTranslator()
    samples = [
        {"id": 1, "text_original": "敢动我啊 都人", "speaker": "តួប្រុស (ពិសិដ្ឋ)", "voice": "piseth"},
        {"id": 2, "text_original": "送什么", "speaker": "តួស្រី (ស្រីមុំ)", "voice": "sreymom"},
        {"id": 3, "text_original": "你是怕我在你爸面前插船你们吗 你们竟然敢打我们满灵", "speaker": "តួស្រី (ស្រីមុំ)", "voice": "sreymom"},
        {"id": 4, "text_original": "但是你", "speaker": "តួប្រុស (ពិសិដ្ឋ)", "voice": "piseth"},
        {"id": 5, "text_original": "我才是老板", "speaker": "តួស្រី (ស្រីមុំ)", "voice": "sreymom"},
        {"id": 6, "text_original": "我就知道了", "speaker": "តួស្រី (ស្រីមុំ)", "voice": "sreymom"},
        {"id": 7, "text_original": "没关系", "speaker": "តួប្រុស (ពិសិដ្ឋ)", "voice": "piseth"},
        {"id": 8, "text_original": "是不是傻", "speaker": "តួស្រី (ស្រីមុំ)", "voice": "sreymom"},
        {"id": 9, "text_original": "曹早", "speaker": "តួប្រុស (ពិសិដ្ឋ)", "voice": "piseth"},
    ]
    res = await tr.translate_dialogues(samples, mode="drama_dubbing", source_lang="zh")
    with open("scratch_trans_test.txt", "w", encoding="utf-8") as out:
        for item in res:
            out.write(f"[{item['id']}] {item['speaker']} ({item['voice']})\n")
            out.write(f"   ZH: {item['text_original']}\n")
            out.write(f"   KM: {item['text_km']}\n\n")
    print("Test passed! Wrote to scratch_trans_test.txt")

if __name__ == "__main__":
    asyncio.run(test())
