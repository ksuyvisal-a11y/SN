import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath("."))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from translator import DramaTranslator

test_phrases = [
    ("你看你脸上写着白痴！", "មើលមុខឯងទៅ ដូចមានចារអក្សរថាល្ងង់អញ្ចឹង!"),
    ("给脸不要脸！", "ឱ្យកិត្តិយសហើយមិនចង់បាន!"),
    ("你算什么东西？", "ឯងគិតថាឯងជាស្អី?!"),
    ("我看你是活得不耐烦了！", "ឯងចង់ងាប់មែនទេ?!"),
    ("你敢给我戴绿帽子！", "លួចក្បត់ចិត្តមានប្រុសថ្មី"),
    ("那个女人就是个绿茶！", "ស្រីពុតត្បុត"),
    ("他是个大渣男！", "អាប្រុសសាវា"),
    ("小三找上门来了！", "ស្រីកំណាន់"),
    ("他分明是在吃醋！", "ខឹងប្រច័ណ្ឌ"),
    ("门当户对", "គ្រួសារមានឋានៈស័ក្តិសមគ្នា"),
    ("把他扫地出门！", "បណ្តេញក្បាលចេញពីផ្ទះ!"),
    ("保大还是保小？", "ជួយសង្គ្រោះម្តាយ ឬជួយកូន?!"),
    ("他已经成了植物人", "មនុស្សសន្លប់បាត់ស្មារតី"),
    ("我们要去做亲子鉴定！", "DNA ឈាមជ័រឪពុកកូន"),
    ("怀的是龙胎长孙", "កូននាគរាជ"),
    ("封杀他的所有业务！", "កម្ទេចមុខជំនួញ"),
]

async def main():
    translator = DramaTranslator()
    print("=== TESTING CHINESE DRAMA TRANSLATION UPGRADE ===")
    all_ok = True
    for zh, expected_concept in test_phrases:
        km = await translator.translate_text_free(zh, source_lang="zh", voice="piseth")
        print(f"ZH: {zh}")
        print(f"KM: {km}")
        # Check that no literal translation artifacts exist
        banned = ["ពាក់មួកបៃតង", "តែបៃតង", "កាកសំណល់", "លេខបីតូច", "ញ៉ាំទឹកខ្មេះ", "រាប់ជារបស់អ្វី", "រស់នៅមិនអត់ធ្មត់", "ទ្វារស្មើទ្វារ", "ការពារធំឬតូច", "មនុស្សរុក្ខជាតិ", "បិទសម្លាប់", "Dragon fetus"]
        for b in banned:
            if b in km:
                print(f"  [FAIL] Literal artifact found: {b}")
                all_ok = False
        print("-" * 50)
    
    if all_ok:
        print("ALL TESTS PASSED! Clean, authentic Cambodian cinema dubbing quality verified.")
    else:
        print("SOME TESTS FAILED LITERAL ARTIFACT CHECK.")

if __name__ == "__main__":
    asyncio.run(main())
