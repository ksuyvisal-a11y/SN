import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath("."))

from translator import DramaTranslator

async def main():
    t = DramaTranslator()
    print('Groq keys loaded:', len(t.groq_keys))
    print('Active key:', t.get_active_groq_key()[:12] + '...')
    dialogues = [
        {'id': 1, 'start': 0.0, 'end': 3.0, 'text_original': '总裁，这是最新的财务报告。', 'speaker': '秘书', 'voice': 'sreymom'},
        {'id': 2, 'start': 3.2, 'end': 6.0, 'text_original': '很好，把这份文件交给张昭经理。', 'speaker': '总裁', 'voice': 'piseth'}
    ]
    res = await t.translate_dialogues(dialogues, mode='drama_dubbing', source_lang='zh')
    for r in res:
        line = f"[{r.get('voice')}] {r.get('speaker')}: {r.get('text_km')}\n"
        sys.stdout.buffer.write(line.encode('utf-8'))

if __name__ == '__main__':
    asyncio.run(main())
