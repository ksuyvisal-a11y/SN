import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding='utf-8')

from translator import DramaTranslator

test_phrases = [
    ("我是公司总住", "piseth"),
    ("就算你真是公司的老板呀 也没有开出我的全县", "piseth"),
    ("坏了云京集团老板的孩子", "sreymom"),
    ("什么林", "piseth"),
    ("我在公司被人欺负了", "sreymom"),
    ("能不能开除的吗", "sreymom"),
    ("你怀着孩子呢", "sreymom"),
    ("有空了就回家吃饭啊", "sreymom"),
    ("放心吧 阿姨", "sreymom"),
    ("别动了", "piseth"),
    ("好", "sreymom"),
    ("是", "piseth")
]

async def main():
    t = DramaTranslator()
    print("Testing Drama Translation Quality:")
    for zh, voice in test_phrases:
        km = await t.translate_text_free(zh, source_lang="zh", voice=voice)
        print(f"ZH: {zh:30} ({voice}) --> KM: {km}")

asyncio.run(main())
