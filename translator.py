"""
Drama & Movie Recap Contextual Translation Engine for Chinese, Korean, English -> Khmer
Specialized in Authentic Cambodian Television Drama Dubbing (ភាសាបញ្ចូលសំឡេងរឿងភាគបែបខ្មែរ)
Strictly Two Professional Voices: ពិសិដ្ឋ (Piseth - Male Lead) and ស្រីមុំ (Sreymom - Female Lead)
"""
import os
import re
import json
import httpx
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

DRAMA_PROMPT_SYSTEM = """You are a master Cambodian film dubbing scriptwriter and voice director specializing in Asian TV dramas (Chinese, Korean, Thai).
Translate dialogue lines into deeply emotional, authentic, captivating, natural spoken Khmer film dubbing language (ភាសាបញ្ចូលសំឡេងរឿងភាគទូរទស្សន៍ខ្មែរអាជីព).

STRICT CHARACTER PERSONA, VOICE & EMOTION MODULATION RULES:
1. Multi-Voice Persona Separation:
   Assign 'voice' ('sreymom' for females, 'piseth' for males), 'speaker_role', 'emotion', 'pitch_hz', and 'rate_percent':
   - Female Lead (តួឯកស្រី e.g. 林早早): voice='sreymom', speaker_role='female_lead', pitch_hz=+0 to +4, rate_percent=+3 to +8 (sweet, emotional, earnest).
   - Villainess / Sarcastic Sister-in-law (ស្រីកំណាច / ឌឺដង e.g. 沈曼琳, 恶毒配角): voice='sreymom', speaker_role='villainess', pitch_hz=+16 to +22 (piercing, sharp, haughty), rate_percent=+14 to +18 (fast, sneering).
   - Mother-in-Law / Elder Female (ម្តាយក្មេក e.g. 婆婆, 夫人, 恶婆婆): voice='sreymom', speaker_role='mother_in_law', pitch_hz=-16 to -22 (heavy, deep, stern), rate_percent=-4 to -8 (authoritative, measured).
   - Male Lead / CEO (តួឯកប្រុស / លោកប្រធាន e.g. 李沐谦): voice='piseth', speaker_role='male_lead', pitch_hz=-8 to -14 (deep, commanding, rich resonance), rate_percent=+0 to +4.
   - Furious / Shouting Male (ឈុតឈ្លោះ / ស្រែកគំហក): voice='piseth', speaker_role='male_angry', pitch_hz=+12 to +16, rate_percent=+18 to +24 (aggressive, intense).
   - Elder Male / Butler / Father (ឪពុក / 伯父 / 爷爷): voice='piseth', speaker_role='male_elder', pitch_hz=-18 to -24, rate_percent=-6 to -10.
   - Subordinate / Assistant (ជំនួយការ / 张昭 / 保安): voice='piseth', speaker_role='subordinate', pitch_hz=0, rate_percent=+5.

2. CRITICAL TRANSLATION ACCURACY & DRAMA IDIOMS:
   - "看你脸上写着白痴" ➔ "មើលមុខឯងទៅ ដូចមានចារអក្សរថាល្ងង់អញ្ចឹង!" (NEVER translate as "កង្វល់" or "កំប្លែង"!).
   - "龙胎" ➔ "កូននាគរាជ" or "ឈាមជ័រត្រកូលអភិជន" (NEVER translate as English "Dragon fetus"!).
   - "按摩店" ➔ "ហាងម៉ាស្សា" (NEVER translate as "ក្រុមហ៊ុន Anmo Electric"!).
   - "戴绿帽子 / 戴绿帽" ➔ "លួចក្បត់ចិត្តមានប្រុសថ្មី" or "លួចមានសាហាយ" (NEVER translate literally as "ពាក់មួកបៃតង"!).
   - "绿茶 / 绿茶婊" ➔ "ស្រីពុតត្បុត" or "ស្រីមុខស្ងួតចិត្តពិសពុល" (NEVER translate as "តែបៃតង"!).
   - "渣男" ➔ "អាប្រុសសាវា" or "ប្រុសព្រានចិត្តខ្មៅ" (NEVER translate as "បុរសកាកសំណល់"!).
   - "小三 / 第三者" ➔ "ស្រីកំណាន់" or "ជនទីបីបំផ្លាញស្នេហា" (NEVER translate as "លេខបីតូច"!).
   - "吃醋" ➔ "ខឹងប្រច័ណ្ឌ" (NEVER translate as "ញ៉ាំទឹកខ្មេះ"!).
   - "备胎" ➔ "មនុស្សសម្រាប់កំដរអារម្មណ៍" (NEVER translate as "កង់ឡានបម្រុង"!).
   - "白月光" ➔ "ស្នេហាដំបូងមិនអាចបំភ្លេចបាន" (NEVER translate as "ពន្លឺព្រះច័ន្ទពណ៌ស"!).
   - "假戏真做" ➔ "សម្តែងយូរៗទៅក្លាយជាស្នេហាពិត" (NEVER translate as "សម្តែងក្លែងក្លាយក្លាយជាពិត"!).
   - "契约婚姻" ➔ "រៀបការក្លែងក្លាយតាមកិច្ចសន្យា".
   - "给脸不要脸" ➔ "ឱ្យកិត្តិយសហើយមិនចង់បាន!" or "ឱ្យមុខមិនចង់បានមុខ!".
   - "算什么东西" ➔ "ឯងគិតថាឯងជាស្អី?!" or "ឯងជាស្អីឱ្យប្រាកដហ្នឹង?!" (NEVER translate as "រាប់ជារបស់អ្វី"!).
   - "活得不耐烦了" ➔ "ឯងចង់ងាប់មែនទេ?!" or "មិនចង់រស់នៅស្រួលទេមែនទេ?!" (NEVER translate as "រស់នៅមិនអត់ធ្មត់"!).
   - "狗仗人势" ➔ "អាពឹងអំណាចចៅហ្វាយ!" or "ឆ្កែព្រុសអាងកន្ទុយ!" (NEVER translate as "ឆ្កែអាងមនុស្ស"!).
   - "狗眼看人低" ➔ "មើលងាយមនុស្សពេកហើយ!" (NEVER translate as "ភ្នែកឆ្កែមើលមនុស្សទាប"!).
   - "野种 / 野孩子" ➔ "កូនឥតខាន់ស្លា!" or "អាឈាមជ័រថោកទាប!" (NEVER translate as "ពូជព្រៃ"!).
   - "让你吃不了兜着走" ➔ "ខ្ញុំនឹងធ្វើឱ្យឯងរងទុក្ខវេទនាមិនខាន!".
   - "门当户对" ➔ "គ្រួសារមានឋានៈស័ក្តិសមគ្នា" (NEVER translate as "ទ្វារស្មើទ្វារ"!).
   - "豪门" ➔ "ត្រកូលអភិជន" or "គ្រួសារមហាសេដ្ឋី" (NEVER translate as "ទ្វារអ្នកមាន"!).
   - "扫地出门" ➔ "បណ្តេញក្បាលចេញពីផ្ទះ!" (NEVER translate as "បោសដីចេញក្រៅ"!).
   - "赘婿 / 倒插门" ➔ "កូនប្រសារចូលស្តី" (NEVER translate as "កូនប្រសារផ្ញើខ្លួន"!).
   - "扮猪吃老虎" ➔ "ធ្វើពុតជាកំសោយដើម្បីវាយបក" (NEVER translate as "ធ្វើពុតជាជ្រូកស៊ីខ្លា"!).
   - "保大还是保小" ➔ "ជួយសង្គ្រោះម្តាយ ឬជួយកូន?!" (NEVER translate as "ការពារធំឬតូច"!).
   - "植物人" ➔ "មនុស្សសន្លប់បាត់ស្មារតី" (NEVER translate as "មនុស្សរុក្ខជាតិ"!).
   - "亲子鉴定" ➔ "ការធ្វើតេស្ត DNA ឈាមជ័រឪពុកកូន" (NEVER translate as "ការកំណត់អត្តសញ្ញាណឪពុកម្តាយកូន"!).
   - "封杀" ➔ "កម្ទេចមុខជំនួញ" or "បិទផ្លូវរកស៊ី" (NEVER translate as "បិទសម្លាប់"!).
   - "鸠占鹊巢" ➔ "ចោរដណ្តើមទ្រព្យម្ចាស់" or "ដណ្តើមតំណែងគេ".
   - "李沐谦" ➔ "លីមូឈៀន", "林早早" ➔ "លីនចាវចាវ", "沈曼琳" ➔ "សិនម៉ាន់លីង", "张昭" ➔ "ចាងចាវ", "林嫂嫂" ➔ "បងថ្លៃស្រីលីន", "曹早" ➔ "ឆាវចាវ".
   - "你瞎了" ➔ "ឯងខ្វាក់ភ្នែកមែនទេ?!", "找死" ➔ "ចង់ងាប់មែនទេ?!", "肚子里的孩子" ➔ "កូននៅក្នុងពោះខ្ញុំ", "长孙" ➔ "ចៅប្រុសច្បង".

3. HIERARCHICAL PRONOUNS & RELATIONSHIPS:
   - Boss & Employee: Boss calls subordinate "ឯង" or "អ្នកគ្រប់គ្រង...", subordinate calls boss "លោកប្រធាន" / "ខ្ញុំ".
   - Husband & Wife: "បង" vs "អូន" (NEVER call male lead "ប្រពន្ធខ្ញុំ" or female lead "ប្តីខ្ញុំ").
   - Bitter Enemies in Arguments: "ឯង / នាងឯង" vs "យើង / ខ្ញុំ".
   - Mother-in-Law & Daughter-in-Law: "ម៉ែ" vs "នាងឯង / កូន".

4. TIMING & SCRIPT DURATION ADAPTATION (កំណត់ប្រវែងឃ្លាឱ្យត្រូវនឹង Timecode):
   - Input items include 'duration' (seconds).
   - SHORT LINES (duration <= 1.2s or 1-3 character commands e.g. 滚, 走, 站住, 住手, 救命, 闭嘴, 谁啊): translate into SHORT, PUNCHY Khmer words (1-3 words max, e.g. "ចេញទៅ!", "ឈប់ភ្លាម!", "ទៅ!", "ជួយផង!", "បិទមាត់!"). NEVER expand short shouts into long sentences. Lip-sync MUST finish when the character's mouth closes!
   - LONG LINES (duration >= 3.0s): translate with natural dramatic cadence matching the speaking duration.
   - Syllables and spoken length of text_km must strictly match the actor's mouth movement window.

5. Output Format: Valid JSON with key 'dialogues' containing array of objects:
   {"id": int, "start": float, "end": float, "text_original": str, "text_km": str, "speaker": str, "speaker_role": str, "emotion": str, "voice": "piseth"|"sreymom", "rate_percent": int, "pitch_hz": int}
"""

DRAMA_PROMPT_SINGLE_VOICE = """You are a master Cambodian television drama solo narrator (អ្នកបញ្ចូលសំឡេងរឿងទោលអាជីព).
Translate dialogue lines into deeply emotional, authentic, captivating, natural spoken Khmer film dubbing language (ភាសាបញ្ចូលសំឡេងរឿងភាគបែបខ្មែរពិរោះរណ្តំ).

STRICT SINGLE VOICE DUBBING RULES (សំឡេងទោលតែមួយគត់):
1. Single Voice Base: Voice identifier is strictly '{VOICE}' for ALL lines.
2. Unified Stable Pitch & Rate: pitch_hz is strictly 0. rate_percent is strictly 0.
   Do NOT modulate pitch to high or low frequencies. Keep the voice 100% natural, unified, and consistent throughout the entire film.
3. Single Continuous Breath (១ ដង្ហើមជាប់គ្នា):
   Write each dialogue line to be delivered in ONE continuous, natural, seamless breath without internal comma pauses or interruptions.
4. SCRIPT DURATION ADAPTATION (Lip-Sync):
   - Short lines (duration <= 1.2s): translate into 1-3 punchy words (e.g. "ចេញទៅ!", "ឈប់!", "ជួយផង!"). Never expand into long sentences.
   - Long lines (duration >= 3.0s): translate with natural flow matching the mouth movement duration.

5. CRITICAL TRANSLATION ACCURACY & DRAMA IDIOMS:
   - "看你脸上写着白痴" ➔ "មើលមុខឯងទៅ ដូចមានចារអក្សរថាល្ងង់អញ្ចឹង!" (NEVER translate as "កង្វល់" or "កំប្លែង"!).
   - "龙胎" ➔ "កូននាគរាជ" or "ឈាមជ័រត្រកូលអភិជន" (NEVER translate as English "Dragon fetus"!).
   - "按摩店" ➔ "ហាងម៉ាស្សា" (NEVER translate as "ក្រុមហ៊ុន Anmo Electric"!).
   - "戴绿帽子 / 戴绿帽" ➔ "លួចក្បត់ចិត្តមានប្រុសថ្មី" or "លួចមានសាហាយ" (NEVER translate literally as "ពាក់មួកបៃតង"!).
   - "绿茶 / 绿茶婊" ➔ "ស្រីពុតត្បុត" or "ស្រីមុខស្ងួតចិត្តពិសពុល" (NEVER translate as "តែបៃតង"!).
   - "渣男" ➔ "អាប្រុសសាវា" or "ប្រុសព្រានចិត្តខ្មៅ" (NEVER translate as "បុរសកាកសំណល់"!).
   - "小三 / 第三者" ➔ "ស្រីកំណាន់" or "ជនទីបីបំផ្លាញស្នេហា" (NEVER translate as "លេខបីតូច"!).
   - "吃醋" ➔ "ខឹងប្រច័ណ្ឌ" (NEVER translate as "ញ៉ាំទឹកខ្មេះ"!).
   - "备胎" ➔ "មនុស្សសម្រាប់កំដរអារម្មណ៍" (NEVER translate as "កង់ឡានបម្រុង"!).
   - "白月光" ➔ "ស្នេហាដំបូងមិនអាចបំភ្លេចបាន" (NEVER translate as "ពន្លឺព្រះច័ន្ទពណ៌ស"!).
   - "假戏真做" ➔ "សម្តែងយូរៗទៅក្លាយជាស្នេហាពិត" (NEVER translate as "សម្តែងក្លែងក្លាយក្លាយជាពិត"!).
   - "契约婚姻" ➔ "រៀបការក្លែងក្លាយតាមកិច្ចសន្យា".
   - "给脸不要脸" ➔ "ឱ្យកិត្តិយសហើយមិនចង់បាន!" or "ឱ្យមុខមិនចង់បានមុខ!".
   - "算什么东西" ➔ "ឯងគិតថាឯងជាស្អី?!" or "ឯងជាស្អីឱ្យប្រាកដហ្នឹង?!" (NEVER translate as "រាប់ជារបស់អ្វី"!).
   - "活得不耐烦了" ➔ "ឯងចង់ងាប់មែនទេ?!" or "មិនចង់រស់នៅស្រួលទេមែនទេ?!" (NEVER translate as "រស់នៅមិនអត់ធ្មត់"!).
   - "狗仗人势" ➔ "អាពឹងអំណាចចៅហ្វាយ!" or "ឆ្កែព្រុសអាងកន្ទុយ!" (NEVER translate as "ឆ្កែអាងមនុស្ស"!).
   - "狗眼看人低" ➔ "មើលងាយមនុស្សពេកហើយ!" (NEVER translate as "ភ្នែកឆ្កែមើលមនុស្សទាប"!).
   - "野种 / 野孩子" ➔ "កូនឥតខាន់ស្លា!" or "អាឈាមជ័រថោកទាប!" (NEVER translate as "ពូជព្រៃ"!).
   - "让你吃不了兜着走" ➔ "ខ្ញុំនឹងធ្វើឱ្យឯងរងទុក្ខវេទនាមិនខាន!".
   - "门当户对" ➔ "គ្រួសារមានឋានៈស័ក្តិសមគ្នា" (NEVER translate as "ទ្វារស្មើទ្វារ"!).
   - "豪门" ➔ "ត្រកូលអភិជន" or "គ្រួសារមហាសេដ្ឋី" (NEVER translate as "ទ្វារអ្នកមាន"!).
   - "扫地出门" ➔ "បណ្តេញក្បាលចេញពីផ្ទះ!" (NEVER translate as "បោសដីចេញក្រៅ"!).
   - "赘婿 / 倒插门" ➔ "កូនប្រសារចូលស្តី" (NEVER translate as "កូនប្រសារផ្ញើខ្លួន"!).
   - "扮猪吃老虎" ➔ "ធ្វើពុតជាកំសោយដើម្បីវាយបក" (NEVER translate as "ធ្វើពុតជាជ្រូកស៊ីខ្លា"!).
   - "保大还是保小" ➔ "ជួយសង្គ្រោះម្តាយ ឬជួយកូន?!" (NEVER translate as "ការពារធំឬតូច"!).
   - "植物人" ➔ "មនុស្សសន្លប់បាត់ស្មារតី" (NEVER translate as "មនុស្សរុក្ខជាតិ"!).
   - "亲子鉴定" ➔ "ការធ្វើតេស្ត DNA ឈាមជ័រឪពុកកូន" (NEVER translate as "ការកំណត់អត្តសញ្ញាណឪពុកម្តាយកូន"!).
   - "封杀" ➔ "កម្ទេចមុខជំនួញ" or "បិទផ្លូវរកស៊ី" (NEVER translate as "បិទសម្លាប់"!).
   - "鸠占鹊巢" ➔ "ចោរដណ្តើមទ្រព្យម្ចាស់" or "ដណ្តើមតំណែងគេ".
   - "李沐谦" ➔ "លីមូឈៀន", "林早早" ➔ "លីនចាវចាវ", "沈曼琳" ➔ "សិនម៉ាន់លីង", "张昭" ➔ "ចាងចាវ".

6. Output Format: Valid JSON with key 'dialogues' containing array of objects:
   {"id": int, "start": float, "end": float, "text_original": str, "text_km": str, "speaker": "{VOICE}", "voice": "{VOICE}", "rate_percent": 0, "pitch_hz": 0}
"""

# Pre-normalization: normalize Chinese drama slang, spoken colloquialisms, and common whisper misrecognitions
CHINESE_DRAMA_PRE_NORM = [
    (r'看你臉[上]?寫著白[痴癡]|看你脸[上]?写着白[痴痴]', '看你脸上写着白痴'),
    (r'白[痴癡]', '白痴'),
    (r'龍胎|龙胎', '龙胎'),
    (r'趙孫|赵孙|長孫|长孙', '长孙'),
    (r'按摩[店館馆]', '按摩店'),
    (r'李[沐幕木][謙谦千]', '李沐谦'),
    (r'林[早曹][早曹]', '林早早'),
    (r'沈曼[琳玲]|沈蔓[琳玲]', '沈曼琳'),
    (r'[幹操草][\s，,]*[動动]了.*', '动了！有动静了！'),
    (r'[幹操草][\s，,]*', ''),
    (r'敦仁', ''),
    (r'送你回去', '陪你回家'),
    (r'送你走', '带你离开'),
    (r'送你', '陪你'),
    (r'送什么', '到底要送去哪里啊，我哪里都不去！'),
    (r'跟[你您]送', '提醒你'),
    (r'^(?:快)?走[!！。]?$', '快走！'),
    (r'^走吧[!！。]?$', '走吧！'),
    (r'我也下了|你也下了', '你也害怕了'),
    (r'我也瞎了|你也瞎了', '你也眼瞎了'),
    (r'想擦', '想逃跑'),
    (r'罷面前', '爸面前'),
    (r'插船你們嗎|插船你们吗', '拆穿你们吗'),
    (r'滿臨|满临|滿靈|满灵', '曼玲'),
    (r'不曉得了|不晓得了', '不想活了'),
    (r'張柔哥|張潮哥|张潮哥|林森哥|張宗哥|张宗哥', '张潮哥'),
    (r'在個路上|在个路上', '在路上'),
    (r'我才是[老闆老板]', '我才是真正的老板！'),
    (r'我就知道了', '我早就知道了！'),
    (r'話可不能亂說|话可不能乱说', '千万别胡说八道！'),
    (r'沒關係|没关系', '没事的不用担心'),
    (r'是不是傻', '你是不是傻子啊'),
    (r'兩張紅的|两张红的', '两百块红钞票'),
    (r'你[瘋疯]了', '你疯了吗'),
    (r'林柱莉|林嫂嫂', '林嫂嫂'),
    (r'你夫人', '你的夫人在这'),
    (r'報告室|报告室', '报案室'),
    (r'你這樣的破售品|你这样的破售品', '像你这样的废物'),
    (r'你進攻認識了|你进攻认识了', '你知道认罪了吗'),
    (r'曹早', '曹早！'),
    (r'想得美', '别白日做梦了'),
    (r'放肆', '放肆！'),
    (r'住手', '住手！'),
    (r'救命', '救命！'),
    (r'閉嘴|闭嘴', '闭嘴！'),
    (r'滾|滚', '滚！'),
    (r'憑什麼|凭话', '你凭什么这么做'),
    (r'等著瞧|等着瞧', '你给我等着瞧'),
    (r'聽到了嗎|听到了吗', '听清楚了没有'),
    (r'別碰我|别碰我', '别碰我！'),
    (r'放開我|放开我', '放开我！'),
    (r'怎麼可能|怎么可能', '这绝不可能'),
    (r'真的嗎|真的吗', '这是真的吗'),
    (r'胡說八道', '全是胡说八道'),
    (r'少廢話|少废话', '少废话！'),
    (r'算了吧', '就到此为止吧'),
    (r'對不起|对不起', '我真的很对不起'),
    (r'我錯了|我错了', '我知道错了'),
    (r'帶走|带走', '把人带走'),
    (r'站住', '站住！'),
    (r'你敢', '你敢动一下试试'),
    (r'誰啊|谁啊', '到底是谁啊'),
    (r'怎麼辦|怎么办', '现在该怎么办啊'),
    (r'你在[幹干]什麼|你在[幹干]什么|[幹干]什麼|[幹干]什么', '你到底在干什么啊'),
    (r'在哪[裡里]|在哪里', '到底在哪里啊'),
    (r'快[點点]|快点', '快点！'),
    (r'等等我', '等等我！先别走'),
    (r'禮幕前|礼幕前|李幕千', '李慕千'),
    (r'伯儿|伯兒', '伯父'),
    # Drama idioms and slang pre-normalization
    (r'戴[綠绿]帽[子]?', '跟别的男人偷情出轨'),
    (r'[綠绿]茶[婊]?', '心机恶毒女人'),
    (r'渣男', '负心汉渣男'),
    (r'小[三四]|第三者', '破坏婚姻的情妇狐狸精'),
    (r'吃[醋]', '吃醋嫉妒'),
    (r'備胎|备胎', '备选替补情人'),
    (r'白月光', '心中难忘的初恋'),
    (r'假[戲戏]真做', '假戏真做产生了真感情'),
    (r'[契約契约]婚姻', '假结婚契约'),
    (r'給臉不要臉|给脸不要脸|别给脸不要脸|別給臉不要臉', '给脸不要脸'),
    (r'算什麼東西|算什么东西', '你算什么东西'),
    (r'我看你是活得不耐烦[了]?', '我看你是活得不耐烦了找死'),
    (r'活得不耐煩[了]?|活得不耐烦[了]?', '不想活了吗找死'),
    (r'狗仗人勢|狗仗人势', '狗仗人势仗势欺人'),
    (r'狗眼看人低', '狗眼看人低看不起人'),
    (r'野種|野种|野孩子', '私生子野种'),
    (r'吃不了兜著走|吃不了兜着走', '让你吃不了兜着走'),
    (r'[門门][當当][戶户][對对]', '门当户对地位相当'),
    (r'豪[門门]', '顶级富豪名门'),
    (r'[掃扫]地出[門门]', '赶出家门扫地出门'),
    (r'上[門门]女[婿]|贅婿|赘婿|倒插[門门]', '入赘的上门女婿'),
    (r'扮[豬猪]吃老虎', '扮猪吃老虎隐藏实力'),
    (r'保大[還还]是保小|保大保小', '救保母亲还是救保婴儿'),
    (r'植物人', '重度昏迷不醒的植物人'),
    (r'親子[鑑鉴]定|亲子鉴定', 'DNA亲子鉴定血缘'),
    (r'胎死腹中', '婴儿死在腹中胎死'),
    (r'封[殺杀]', '封杀封锁业务'),
    (r'鳩佔鵲巢|鸠占鹊巢', '鸠占鹊巢霸占财产'),
]

# Post-translation polish: convert machine-translated Khmer into natural Khmer TV Drama Dubbing
KHMER_DUBBING_POST_CLEANUP = [
    # Guard against bad machine translation relics
    (r'(?i)dragon\s*fetus', 'កូននាគរាជ'),
    (r'(?i)(?:ក្រុមហ៊ុន\s*)?anmo\s*(?:electric)?', 'ហាងម៉ាស្សា'),
    (r'ចាក់កូវិស័យរបស់\s*លីន\s*មីឆេន', 'គ្រួសាររបស់លោកលីមូឈៀន'),
    (r'លី\s*មីឆេន|លី\s*មូឆៀន|លី\s*ម៉ូឈៀន', 'លីមូឈៀន'),
    (r'លីន\s*ចាវ\s*ចាវ|លីន\s*ចៅ\s*ចៅ', 'លីនចាវចាវ'),
    (r'សិន\s*ម៉ាន់\s*លីង|សិន\s*ម៉ាន់\s*លីន', 'សិនម៉ាន់លីង'),
    (r'មើលមុខឯង.*កង្វល់.*', 'មើលមុខឯងទៅ ដូចមានចារអក្សរថាល្ងង់អញ្ចឹង!'),
    # Targeted Machine Translation Artifacts & Spoken Khmer Cinema Cleanups
    (r'ស្ថានភាពលូតលាស់(?:ធ្ងន់ធ្ងរ)?|ស្ថានភាពរុក្ខជាតិ', 'មនុស្សសន្លប់បាត់ស្មារតី'),
    (r'របស់\s*កូន\s*នាគរាជ', 'ជាកូននាគរាជ'),
    (r'គភ៌នាគ|ទារកនាគ', 'កូននាគរាជ'),
    (r'(?:ធ្វើ\s*)?តេស្ត\s*(?:ឌីអិនអេ|DNA)\s*(?:ប៉ាប៉ា|ឪពុក|ម្តាយ)?(?!\s*ពិនិត្យ)', 'ធ្វើតេស្ត DNA ពិនិត្យឈាមជ័រឪពុកកូន'),
    (r'(?:ហ៊ាន\s*)?(?:សាកល្បង\s*)?មាន\s*ស្នេហា\s*ជាមួយ\s*ប្រុស\s*ផ្សេង|ម៉េចក៏ហ៊ានជេរខ្ញុំ', 'ហ៊ានលួចក្បត់ចិត្តមានប្រុសថ្មីផង?!'),
    (r'(?:ធ្វើ\s*សកម្មភាព\s*)?បោក\s*ខ្ញុំ(?:ក្បត់)?', 'លួចក្បត់ចិត្តមានប្រុសថ្មី'),
    (r'ស្ត្រី\s*នោះ\s*ជា\s*ស្ត្រី.*គំនិត\s*អាក្រក់.*|ស្ត្រី\s*(?:ដែល\s*)?មាន\s*គំនិត\s*អាក្រក់|ស្ត្រី\s*គំនិត\s*អាក្រក់', 'មីស្រីម្នាក់នោះជាស្រីពុតត្បុតពិសពុល!'),
    (r'គាត់ជា\s*មនុស្ស\s*ល្ងង់\s*ខ្លៅ[!?.]*|ឯង\s*បោកប្រាស់\s*ដ៏\s*ធំ|មនុស្ស\s*បោកប្រាស់\s*ដ៏\s*ធំ|បុរស\s*បោកប្រាស់\s*ដ៏\s*ធំ', 'គាត់ជាអាប្រុសសាវា!'),
    (r'ម្ចាស់ស្រី(?:ដែលបំផ្លាញអាពាហ៍ពិពាហ៍)?|ម្ចាស់ស្រីដែលបំផ្លាញគ្រួសារ', 'ស្រីកំណាន់'),
    (r'ដេញ\s*គាត់\s*ចេញ\s*ពី\s*ផ្ទះ\s*ហើយ\s*ដេញ\s*គាត់\s*ចេញ[!?.]*', 'បណ្តេញក្បាលចេញពីផ្ទះភ្លាមទៅ!'),
    (r'ខ្ញុំគិតថា(?:អ្នក|ឯង)មិនចង់រស់(?:នៅ|ស្រួល)?(?:ទេ)?.*', 'ខ្ញុំគិតថាឯងច្បាស់ជាមិនចង់រស់ស្រួលទេ ឯងចង់ងាប់មែនទេ?!'),
    (r'(?:គាត់)?ច្បាស់\s*ជា\s*ច្រណែន[!?.]*', 'គាត់ច្បាស់ជាកំពុងប្រច័ណ្ឌហើយ!'),
    (r'ជួយសង្គ្រោះម្តាយឬទារក', 'ជួយសង្គ្រោះម្តាយ ឬជួយកូន'),
    (r'បិទអាជីវកម្មរបស់គាត់ទាំងអស់', 'កម្ទេចមុខជំនួញរបស់គាត់ទាំងអស់'),
    # 6 Essential Drama Idiom Categories (បកប្រែពាក្យពិបាកៗក្នុងរឿងភាគឱ្យត្រូវន័យខ្មែរ ១០០%)
    (r'ពាក់មួក(?:ពណ៌)?បៃតង', 'លួចក្បត់ចិត្តមានប្រុសថ្មី'),
    (r'មួក(?:ពណ៌)?បៃតង', 'ក្បត់ចិត្តមានប្រុសថ្មី'),
    (r'(?:ស្រី|នាង)?(?:តែ|ទឹកតែ)បៃតង', 'ស្រីពុតត្បុត'),
    (r'បុរសកាកសំណល់|មនុស្សប្រុសកាកសំណល់', 'អាប្រុសសាវា'),
    (r'លេខ(?:បី|៣)តូច|លេខ\s*៣\s*តូច', 'ស្រីកំណាន់'),
    (r'ញ៉ាំទឹកខ្មេះ|ផឹកទឹកខ្មេះ', 'ខឹងប្រច័ណ្ឌ'),
    (r'កង់(?:ឡាន)?បម្រុង', 'មនុស្សកំដរអារម្មណ៍'),
    (r'ពន្លឺព្រះច័ន្ទ(?:ពណ៌)?ស', 'ស្នេហាដំបូងដក់ជាប់ក្នុងចិត្ត'),
    (r'សម្តែងក្លែងក្លាយក្លាយជាពិត|ក្លែងក្លាយក្លាយជាការពិត', 'សម្តែងយូរៗទៅស្រឡាញ់ពិតមែន'),
    (r'អាពាហ៍ពិពាហ៍កិច្ចសន្យា|កិច្ចសន្យាអាពាហ៍ពិពាហ៍', 'រៀបការក្លែងក្លាយតាមកិច្ចសន្យា'),
    (r'(?:ឱ្យ|ឲ្យ|ផ្តល់)មុខមិនចង់បានមុខ', 'ឱ្យកិត្តិយសហើយមិនចង់បាន!'),
    (r'រាប់ជារបស់អ្វី|គិតជារបស់អ្វី', 'ឯងគិតថាឯងជាស្អី?!'),
    (r'រស់នៅ(?:ដោយ)?មិនអត់ធ្មត់', 'ឯងចង់ងាប់មែនទេ?!'),
    (r'ឆ្កែ(?:ពឹង|អាង)(?:អំណាច)?មនុស្ស', 'អាពឹងអំណាចចៅហ្វាយ!'),
    (r'ភ្នែកឆ្កែមើលមនុស្សទាប', 'មើលងាយមនុស្សពេកហើយ!'),
    (r'ពូជព្រៃ|កូនក្មេងព្រៃ|កូនព្រៃ', 'កូនឥតខាន់ស្លា!'),
    (r'ញ៉ាំមិនអស់វេចទៅ', 'ខ្ញុំនឹងធ្វើឱ្យឯងរងទុក្ខវេទនាមិនខាន!'),
    (r'ទ្វារស្មើ(?:គ្នានឹង)?ទ្វារ', 'គ្រួសារមានឋានៈស័ក្តិសមគ្នា'),
    (r'ទ្វារអ្នកមាន(?:ទ្រព្យ)?', 'ត្រកូលអភិជន'),
    (r'បោសដីចេញ(?:ពី)?ក្រៅ|បោសចេញពីទ្វារ', 'បណ្តេញក្បាលចេញពីផ្ទះ!'),
    (r'កូនប្រសារ(?:ផ្ញើខ្លួន|សំពះផ្ទះ|ចូលផ្ទះ)', 'កូនប្រសារចូលស្តី'),
    (r'ធ្វើពុតជាជ្រូកស៊ីខ្លា', 'ធ្វើពុតជាកំសោយដើម្បីវាយបក'),
    (r'(?:ការពារ|ជួយសង្គ្រោះ)ធំឬ(?:ការពារ|ជួយសង្គ្រោះ)?តូច', 'ជួយសង្គ្រោះម្តាយ ឬជួយកូន?!'),
    (r'មនុស្សរុក្ខជាតិ', 'មនុស្សសន្លប់បាត់ស្មារតី'),
    (r'ការ(?:កំណត់|ផ្ទៀងផ្ទាត់)អត្តសញ្ញាណឪពុកម្តាយ(?:-|និង)?កូន', 'ការធ្វើតេស្ត DNA ឈាមជ័រឪពុកកូន'),
    (r'ស្លាប់គភ៌ក្នុងពោះ', 'កូនស្លាប់ក្នុងពោះ'),
    (r'បិទសម្លាប់(?:មុខជំនួញ)?', 'កម្ទេចមុខជំនួញ'),
    (r'ចោរដណ្តើមទ្រព្យម្ចាស់|សត្វកុកដណ្តើមសំបុកចាប', 'ចោរដណ្តើមទ្រព្យសម្បត្តិគេ'),
    # 1. Compact lip-sync friendly drama lines for short utterances (រក្សាប្រវែងឃ្លាឱ្យសមស្របនឹង Timecode)
    (r'^ដើរ[។!.]*$', 'ចេញទៅ!'),
    (r'^(?:ឆាប់)?ដើរទៅ[។!.]*$', 'ចេញទៅ!'),
    (r'^ល្អ[។!.]*$', 'ល្អ!'),
    (r'^បាទ[។!.]*$', 'បាទ!'),
    (r'^ចាស[។!.]*$', 'ចាស!'),
    (r'^ទេ[។!.]*$', 'ទេ!'),
    (r'^ឈប់[។!.]*$', 'ឈប់ភ្លាម!'),
    (r'^លឿន[។!.]*$', 'ឆាប់ឡើង!'),
    (r'^ប្រយ័ត្ន[។!.]*$', 'ប្រយ័ត្នខ្លួន!'),
    (r'^គាត់[។!.]*$', 'គាត់មែនទេ?!'),
    (r'^ប៉ា[។!.]*$', 'លោកប៉ា!'),
    (r'^ម៉ាក់[។!.]*$', 'អ្នកម៉ាក់!'),
    (r'^ស្អី[។!.]*$', 'ស្អីគេ?!'),
    (r'^អ្វី[។!?]*$', 'ស្អីគេ?!'),
    (r'^ម៉េច[។!.]*$', 'ម៉េចក៏ចឹង?!'),
    (r'^ជួយ[។!.]*$', 'ជួយផង!'),
    (r'^មិនអីទេ[។.]*$', 'មិនអីទេ!'),
    (r'^សុំទោស[។.]*$', 'ខ្ញុំសុំទោស!'),
    (r'^ដឹងហើយ[។.]*$', 'ខ្ញុំដឹងហើយ!'),
    (r'^ចេញទៅ[។!.]*$', 'ចេញទៅ!'),
    (r'^ខ្ញុំជាចៅហ្វាយ[។.]*$', 'ខ្ញុំនេះទើបជាថៅកែពិតប្រាកដ!'),
    (r'^ខ្ញុំបានដឹងពីវា[។.]*$', 'ខ្ញុំដឹងតាំងពីដំបូងមកម្ល៉េះ!'),
    (r'^កុំនិយាយមិន.*$', 'កុំនិយាយផ្តេសផ្តាសឱ្យសោះណា!'),
    (r'^នេះគឺជា Zengjin របស់ខ្ញុំ[។.]*$', 'នេះជាភស្តុតាងរបស់ខ្ញុំពិតប្រាកដ!'),
    (r'^ក្រហមពីរ[។.]*$', 'លុយក្រដាសក្រហមពីរសន្លឹក!'),
    (r'^អ្នកឯងឆ្កួតហើយមែនទេ.*$', 'ឯងឆ្កួតហើយមែនទេ?!'),
    (r'^អ្នកឆ្កួតហើយមែនទេ.*$', 'ឯងឆ្កួតហើយមែនទេ?!'),
    (r'^លីន ជូលី.*$', 'លីនជូលី! នាងយ៉ាងម៉េចហើយ?!'),
    (r'^Lin Zhuli.*$', 'លីនជូលី! នាងដឹងខ្លួនហើយមែនទេ?!'),
    (r'^ប្រពន្ធរបស់អ្នក[។.]*$', 'អ្នកស្រីជាភរិយារបស់លោក!'),
    (r'^វាមិនសំខាន់ទេ[។.]*$', 'មិនអីនោះទេ មិនបាច់បារម្ភទេ!'),
    (r'^បន្ទប់បង្រៀន[។.]*$', 'បន្ទប់រាយការណ៍!'),
    (r'^ល្ងង់មែនទេ.*$', 'ឯងឆ្កួតឬក៏ល្ងង់ឱ្យប្រាកដហ្នឹង?!'),
    (r'^បំណែកនៃសំរាមដូចអ្នក[។.]*$', 'មនុស្សអត់បានការដូចជាឯង!'),
    (r'^អ្នកដឹងពីបទល្មើស[។.]*$', 'ឯងដឹងពីកំហុសខ្លួនឯងហើយនៅ?!'),
    (r'^Cao Zao[។.]*$', 'លោកឆាវចាវ! ឆាប់មកទីនេះភ្លាម!'),
    (r'^ស្បែកជើងនៅលើមុខរបស់ខ្ញុំគឺចម្លែក[។.]*$', 'មុខឯងមិនចេះខ្មាសគេសោះ!'),
    (r'^Angel Law Gong Tiao Guan ខ្ញុំដឹង[។.]*$', 'មន្ត្រីច្បាប់អយ្យការដែលខ្ញុំស្គាល់...'),
    (r'^តើកូននាគរបស់អ្នកជានរណា.*$', 'តើនរណាជាកូនភ្លោះរបស់ឯងឱ្យប្រាកដ?!'),
    (r'^Lin Zhuli ករណីឪពុក[។.]*$', 'រឿងលោកឪពុករបស់លីនជូលី!'),
    (r'^JCPOA បានបញ្ជាក់ថា.*$', 'សាក្សីបញ្ជាក់ថាពួកឯងនៅទីនេះទាំងអស់!'),
    (r'^កន្លែងដែលត្រូវទៅ.*$', 'តើចង់ឱ្យជូនទៅណាទៀតហ្នឹង?! ខ្ញុំមិនទៅណាទាំងអស់!'),
    (r'^(?:ប៉ុន្តែ|តែ)អ្នក[។.]*$', 'ប៉ុន្តែពួកឯងទាំងអស់គ្នា...!'),
    (r'^បូអឺ[។.]*$', 'លោកពូ!'),
    (r'Man\s*Ling|man\s*ling', 'ម៉ានលីង'),
    (r'បងប្អូនក្មេក', 'បងថ្លៃស្រី'),
    (r'អ្នកក៏អាចធ្វើវាបានដែរ', 'ឯងក៏ភ័យញ័រដែរមែនទេ?!'),
    (r'តើអ្នកហ៊ានប៉ះខ្ញុំទេ\??', 'ហ៊ានប៉ះមនុស្សរបស់ខ្ញុំផង ឯងខ្វាក់ភ្នែកហើយមែនទេ?!'),
    (r'^JCPOA បានបញ្ជាក់ថា.*$', 'សាក្សីបញ្ជាក់ថាពួកឯងនៅទីនេះទាំងអស់!'),

    # 2. TV Dubbing Drama Dialogue Replacements
    (r'តើអ្នកកំពុងផ្ញើអ្វី\??', 'តើចង់ឱ្យជូនទៅណាទៀតហ្នឹង?!'),
    (r'ផ្ញើអ្វី\??', 'ជូនស្អីគេ?!'),
    (r'ខ្ញុំកំពុងផ្ញើវាទៅអ្នក[។.]*', 'ខ្ញុំកំពុងតែប្រាប់ឯងហើយតើ!'),
    (r'សុំ​ឱ្យ​គាត់​យក​អ្នក​វិញ​ជា​មុន​សិន', 'ឱ្យគាត់ជូនឯងត្រឡប់ទៅផ្ទះវិញសិនទៅ'),
    (r'យក​អ្នក​វិញ​ជា​មុន​សិន', 'ជូនឯងត្រឡប់ទៅផ្ទះវិញសិន'),
    (r'បងធំនៅខាងក្រៅ', 'បងប្រុសចាងឆាវកំពុងនៅខាងក្រៅ'),
    (r'មិនអីទេ\s*ប្រយ័ត្ន(?:ខ្លួនណា!)*', 'មិនអីទេ ឯងត្រូវប្រយ័ត្នខ្លួនណា!'),
    (r'ផ្លាស់ទី[,.]*', 'មានកម្រើកហើយ! មើល៍!'),
    (r'អ្នកក៏ចុះដែរ[។.]*', 'ឯងក៏ភ័យញ័រដែរមែនទេ?!'),
    (r'ចង់ជូតវា[។.]*', 'ចង់រត់គេចមែនទេ?!'),
    (r'នៅក្នុងជីវិតរបស់ខ្ញុំ\s*Li\s*Muqian', 'មនុស្សដូចខ្ញុំ លីមូឈៀន មួយជីវិតនេះ'),
    (r'Li\s*Muqian|លី\s*មូឈៀន', 'លីមូឈៀន'),
    (r'មិនដែលត្រូវបានគំរាមកំហែង[។.]*', 'មិនដែលឱ្យនរណាមកគំរាមកំហែងបានទេ!'),
    (r'ម៉េចហ៊ានវាយយើង.*', 'ពួកឯងហ៊ានវាយមនុស្សរបស់ខ្ញុំផង?! ថ្លើមធំសម្បើមណាស់!'),
    (r'Man\s*Ling\s*ហ៊ានវាយយើងយ៉ាងម៉េច\??', 'ពួកឯងហ៊ានវាយម៉ានលីងផង?! ថ្លើមធំសម្បើមណាស់!'),
    (r'ខ្ញុំគិតថាអ្នកមិនដឹងទៀតទេ[។.]*', 'ខ្ញុំគិតថាឯងច្បាស់ជាមិនចង់រស់ទេ!'),
    (r'ខ្ញុំគិតថាអ្នកមិនចង់រស់នៅទៀតទេ[។.]*', 'ខ្ញុំគិតថាឯងច្បាស់ជាមិនចង់រស់ទេ!'),
    (r'តើខ្ញុំអាចកាត់អ្នកនៅពីមុខខ្ញុំបានទេ\??', 'ឯងខ្លាចខ្ញុំបកអាក្រាតឯងនៅមុខប៉ាឯងមែនទេ?!'),
    (r'ខ្លាច​ខ្ញុំ​លាតត្រដាង​មុខ​ឪពុក​អ្នក​ទេ\??', 'ឯងខ្លាចខ្ញុំបកអាក្រាតឯងនៅចំពោះមុខប៉ារបស់ឯងមែនទេ?!'),
    (r'ខ្ញុំនឹងលាក់ខ្លួននៅតាមផ្លូវ[។.]*', 'ខ្ញុំនឹងរង់ចាំឯងនៅតាមផ្លូវ!'),
    (r'តើអ្នកខ្វាក់ដែរទេ\??', 'ឯងខ្វាក់ភ្នែកហើយមែនទេ?!'),
    (r'តើអ្នកទៅណា\?\s*តើអ្នកចង់ផ្ញើខ្ញុំទៅណា\?', 'តើចង់ឱ្យជូនទៅណាទៀតហ្នឹង?! ខ្ញុំមិនទៅណាទាំងអស់!'),

    # 3. Question & Exclamation idioms
    (r'អ្វីដែលត្រូវផ្តល់ឱ្យ\s*\?*!*', 'ជូនស្អីគេ?!'),
    (r'តើត្រូវមើលអ្វី\s*\?*!*', 'មើលស្អីហ្នឹង?!'),
    (r'តើត្រូវយំអ្វី\s*\?*!*', 'យំស្អីហ្នឹង?!'),
    (r'តើត្រូវខ្លាចអ្វី\s*\?*!*', 'ខ្លាចស្អីហ្នឹង?!'),
    (r'តើត្រូវរង់ចាំអ្វី\s*\?*!*', 'ចាំស្អីទៀត?!'),
    (r'តើត្រូវហៅអ្វី\s*\?*!*', 'ស្រែកស្អីហ្នឹង?!'),
    (r'តើត្រូវរត់អ្វី\s*\?*!*', 'រត់ស្អីហ្នឹង?!'),
    (r'តើវាជាអ្វី\s*\??', 'ស្អីគេហ្នឹង?!'),
    (r'តើអ្នកកំពុងធ្វើអ្វី\??', 'ឯងចង់ធ្វើស្អីហ្នឹង?!'),
    (r'តើអ្នកចង់យ៉ាងម៉េច\??', 'ឯងចង់យ៉ាងម៉េច?!'),
    (r'តើអ្នកសុខសប្បាយជាទេ\??', 'មិនអីទេមែនទេ?'),
    (r'តើមានអ្វីកើតឡើង\??', 'តើមានរឿងអីកើតឡើង?!'),
    (r'តើវាអាចទៅជារបៀបនេះ\??', 'ហេតុអីបានជាបែបនេះ?!'),
    (r'ហេតុអ្វីបានជាបែបនេះ\??', 'ហេតុអីបានជាបែបនេះ?!'),
    (r'តើអ្នកជារបស់អ្វី\??', 'ឯងជាស្អីឱ្យប្រាកដហ្នឹង?!'),
    (r'តើអ្នកចង់មានន័យយ៉ាងណា\??', 'ឯងចង់មានន័យថាម៉េច?!'),
    (r'តើអ្នកដឹងទេថា', 'ឯងដឹងទេថា'),
    (r'តើអ្នកជឿខ្ញុំទេ\??', 'ឯងជឿខ្ញុំទេ?!'),
    (r'តើវាអាចទៅរួចយ៉ាងដូចម្តេច', 'ម៉េចក៏អាចទៅរួច?!'),

    # 4. Threats & Conflicts
    (r'ឯងក៏ខ្វាក់[។!]*', 'ឯងខ្វាក់ភ្នែកហើយមែនទេ?!'),
    (r'អ្នកក៏ពិការភ្នែកដែរ[។.]*', 'ឯងខ្វាក់ភ្នែកហើយមែនទេ?!'),
    (r'ពិការភ្នែក', 'ខ្វាក់ភ្នែក'),
    (r'មនុស្សអញ', 'មនុស្សរបស់ខ្ញុំ'),
    (r'តើអ្នកហ៊ានប៉ះខ្ញុំទេ\??\s*មានមនុស្សច្រើនណាស់[។.]?', 'ហ៊ានប៉ះមនុស្សរបស់ខ្ញុំផង ឯងខ្វាក់ភ្នែកហើយមែនទេ?!'),
    (r'ហ៊ាន​វាយ​ខ្ញុំ', 'ពួកឯងហ៊ានវាយ'),
    (r'តើអ្នកកំពុងស្វែងរក(?:ការ|សេចក្តី)?ស្លាប់\??', 'ឯងចង់ងាប់មែនទេ?!'),
    (r'ស្វែងរក(?:ការ|សេចក្តី)?ស្លាប់', 'ចង់ងាប់'),
    (r'តើអ្នកចង់ស្លាប់ទេ\??', 'ឯងចង់ងាប់មែនទេ?!'),
    (r'ឆ្កួតហើយ\??', 'ឯងឆ្កួតហើយមែនទេ?!'),
    (r'អ្នកកុហក', 'ឯងកុហក!'),
    (r'អ្នកបោកប្រាស់', 'អាមនុស្សបោកប្រាស់!'),

    # 5. Commands & Quick Action
    (r'រមៀលចេញសម្រាប់ខ្ញុំ', 'ចេញពីទីនេះភ្លាម!'),
    (r'រមៀលចេញ', 'ចេញទៅ!'),
    (r'សមហេតុសមផលតិច', 'កុំនិយាយច្រើនពេក!'),
    (r'ទុកឱ្យខ្ញុំទៅ', 'លែងខ្ញុំភ្លាម!'),
    (r'ជួយសង្គ្រោះជីវិត', 'ជួយផង! ជួយខ្ញុំផង!'),
    (r'កុំមកលើសពីនេះ', 'កុំចូលមក!'),
    (r'ឈប់\s*!', 'ឈប់ភ្លាម!'),
    (r'ប្រយ័ត្ន\s*!', 'ប្រយ័ត្នខ្លួន!'),
    (r'សន្មត\s*!', 'ឈ្លើយណាស់!'),
    (r'មនុស្សចម្លែក', 'មនុស្សប្លែកមុខ'),
    (r'ប្រពន្ធ​ថៅកែ', 'ថៅកែស្រី'),
    (r'គ្រាន់​តែ​យក​គាត់​ទៅ', 'នាំខ្លួនចេញទៅភ្លាម'),
    (r'មិនអាចទៅរួច', 'មិនអាចទៅរួចទេ'),
    (r'និយាយសមហេតុសមផល', 'និយាយផ្តេសផ្តាស'),
    (r'បិទមាត់', 'បិទមាត់ភ្លាម!'),
    (r'ទៅឆ្ងាយ', 'ចេញឱ្យឆ្ងាយភ្លាម!'),
    (r'កុំបារម្ភ', 'កុំភ័យអី'),
    (r'កុំខ្លាច', 'កុំខ្លាចអី'),
    (r'តើអ្នកអាចជួយខ្ញុំបានទេ', 'ជួយខ្ញុំបន្តិចបានទេ'),

    # 6. Naturalizing Mechanical Google-Translate Pronouns & Robotic Phrasing
    (r'តើអ្នកមិនអីទេ\??', 'ឯងមិនអីទេមែនទេ?!'),
    (r'អ្នកមិនអីទេ\??', 'ឯងមិនអីទេមែនទេ?!'),
    (r'\bតើអ្នកកំពុងធ្វើអ្វី\b', 'ឯងកំពុងធ្វើស្អីហ្នឹង?!'),
    (r'\bតើអ្នកចង់បានអ្វី\b', 'ឯងចង់បានស្អី?!'),
    (r'\bតើអ្នកដឹងទេ\b', 'ឯងដឹងទេ?!'),
    (r'\bតើអ្នកជាអ្នកណា\b', 'ឯងជានរណា?!'),
    (r'\bតើអ្នកមកពីណា\b', 'ឯងមកពីណា?!'),
    (r'\bតើអ្នកយល់ទេ\b', 'ឯងយល់ទេ?!'),
    (r'\bតើអ្នកឮទេ\b', 'ឯងឮទេ?!'),
    (r'\bអ្នកសុខសប្បាយជាទេ\b', 'ឯងមិនអីទេមែនទេ?!'),
    (r'\bអ្នកមិនដឹងទេ\b', 'ឯងមិនដឹងរឿងអីទេ!'),
    (r'\bតើអ្នក\b', 'ឯង'),
    (r'\bអ្នកកុំ\b', 'ឯងកុំ'),
    (r'\bអ្នកត្រូវ\b', 'ឯងត្រូវ'),
    (r'\bអ្នកឯង\b', 'ឯង'),
    (r'\bតើត្រូវធ្វើដូចម្តេច\b', 'តើត្រូវធ្វើយ៉ាងម៉េចទៅ?!'),
    (r'\bតើខ្ញុំគួរធ្វើដូចម្តេច\b', 'តើឱ្យខ្ញុំធ្វើយ៉ាងម៉េចទៅ?!'),
    (r'\bតើវាជាការពិតទេ\b', 'ជារឿងពិតមែនទេ?!'),
    (r'\bតើអ្នកកំពុងនិយាយអំពីអ្វី\b', 'ឯងកំពុងនិយាយពីស្អីហ្នឹង?!'),
    (r'\bខ្ញុំមិនខ្វល់\b', 'ខ្ញុំមិនខ្វល់ទេ!'),
    (r'\bកុំខ្វល់ពីខ្ញុំ\b', 'កុំខ្វល់ពីខ្ញុំអី!'),
    (r'\bលែងខ្ញុំ(?!\s*ភ្លាម)\b', 'លែងខ្ញុំភ្លាម!'),
    (r'អនុញ្ញាតឱ្យខ្ញុំទៅ', 'លែងខ្ញុំភ្លាម!'),
    (r'អនុញ្ញាតឱ្យខ្ញុំ', 'លែងខ្ញុំ!'),
    (r'\bកុំប៉ះខ្ញុំ\b', 'កុំប៉ះខ្ញុំឱ្យសោះ!'),
    (r'\bខ្ញុំសុំទោសចំពោះអ្នក\b', 'ខ្ញុំពិតជាសុំទោសឯងខ្លាំងណាស់!'),
    (r'\bចាំខ្ញុំផង\b', 'ចាំខ្ញុំសិន!'),
    (r'\bកុំទៅណា\b', 'កុំទៅណាឱ្យសោះ!'),
    (r'\bជឿខ្ញុំ\b', 'ជឿជាក់លើខ្ញុំទៅ!'),
    (r'\bបំភ្លេចវាទៅ\b', 'បំភ្លេចវាចោលទៅ!'),
    (r'\bចាកចេញពីទីនេះ\b', 'ឆាប់ចេញពីទីនេះភ្លាម!'),
    (r'\bកុំមកជិត\b', 'កុំចូលមកជិតឱ្យសោះ!'),
    (r'\bតើអ្នកបានលឺទេ\b', 'ឯងបានឮច្បាស់ហើយនៅ?!'),
    (r'\bនិយាយម្តងទៀត\b', 'សាកនិយាយម្តងទៀតមើល៍?!'),
    (r'\bខ្ញុំមិនដឹងអ្វីទាំងអស់\b', 'ខ្ញុំមិនដឹងរឿងអីទាំងអស់!'),
    (r'\bកុំធ្វើបាបខ្ញុំ\b', 'កុំធ្វើបាបខ្ញុំអី!'),
    (r'\bខ្ញុំនឹងមិនអត់ទោសឱ្យអ្នក\b', 'ខ្ញុំមិនលើកលែងឱ្យឯងដាច់ខាត!'),
    (r'\bឯងមិនរួចខ្លួនទេ\b', 'ឯងរត់មិនរួចខ្លួនទេ!'),
]

DRAMA_DICTIONARY_FILE = Path("data/drama_dictionary.json")

def load_drama_dictionary() -> Dict[str, str]:
    """Load user-defined character names, titles, and drama vocabulary dictionary."""
    if DRAMA_DICTIONARY_FILE.exists():
        try:
            with open(DRAMA_DICTIONARY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def enrich_khmer_drama_dialogue(
    km_text: str,
    zh_text: str = "",
    voice: str = "piseth",
    duration_sec: Optional[float] = None
) -> str:
    """
    Polishes Khmer drama dialogue into natural, emotional TV dubbing sentences.
    Preserves lip-sync pacing so short lines are punchy and do not bloat into long audio overruns.
    """
    res = km_text.strip()
    if not res:
        return ""

    # Normalize zero-width spaces (\u200b) from Google Translate into standard spacing
    res = re.sub(r'[\s\u200b]+', ' ', res).strip()

    # 0. Direct drama dictionary matching
    if zh_text:
        clean_zh = re.sub(r'[\s!！?？,，.。~～`\'"]+', '', zh_text.strip())
        custom_dict = load_drama_dictionary()
        if clean_zh in custom_dict:
            res = custom_dict[clean_zh]
        else:
            for k, v in custom_dict.items():
                if len(k) >= 3 and k in clean_zh and len(clean_zh) <= len(k) + 4:
                    res = v
                    break

    # Strip trailing artifact words like 'ចាន'
    res = re.sub(r'\s*ចាន[។.!?]*$', '', res)

    # 1. First: clean and normalize punctuation spacing
    res = re.sub(r'([!！])\s*[។.]+', r'\1', res)
    res = re.sub(r'([?？])\s*[។.]+', r'\1', res)
    res = re.sub(r'(?:\?+[!！]+|[!！]+\?+)\s*', '?! ', res)
    res = re.sub(r'[?？](?![!！])\s*', '? ', res)
    res = re.sub(r'[!！](?![?？])\s*', '! ', res)
    res = re.sub(r'[។.]+\s*', '។ ', res)
    res = re.sub(r'\s+', ' ', res).strip()

    # 2. Apply drama idiom dictionary substitutions
    for pattern, replacement in KHMER_DUBBING_POST_CLEANUP:
        if re.search(pattern, res):
            res = re.sub(pattern, replacement, res)

    # 3. Contextual pronoun conversion (avoid robotic 'អ្នក')
    res = re.sub(r'\bតើអ្នកមិនអីទេ[?!។.\s]*', 'ឯងមិនអីទេមែនទេ?! ', res)
    res = re.sub(r'\bអ្នកមិនអីទេ[?!។.\s]*', 'ឯងមិនអីទេមែនទេ?! ', res)
    res = re.sub(r'\bតើអ្នក\b', 'ឯង', res)
    res = re.sub(r'\bអ្នក\b(?!\s*(?:ណា|ស្រី|ប្រុស|ចម្បាំង|និពន្ធ|ជំនួញ))', 'ឯង', res)
    res = re.sub(r'កំដរឯង', 'ជូនឯង', res)
    res = re.sub(r'កំដរអ្នក', 'ជូនឯង', res)
    res = re.sub(r'ផ្ញើខ្ញុំ', 'ជូនខ្ញុំ', res)
    res = re.sub(r'ផ្ញើឯង', 'ជូនឯង', res)
    res = re.sub(r'ផ្ញើអ្នក', 'ជូនឯង', res)
    res = re.sub(r'ទុកខ្ញុំចោល', 'កុំខ្វល់ពីខ្ញុំអី', res)
    res = re.sub(r'ឆាប់ទៅ(?!\w)', 'ឆាប់រត់ទៅ', res)

    # Clean repeated phrase patterns that can occur during chained substitutions
    res = re.sub(r'(?:ភ្លាម[!?\s]*)+', 'ភ្លាម! ', res)
    res = re.sub(r'(?:កុំរត់[!?\s]*)+', 'កុំរត់! ', res)
    res = re.sub(r'(?:ឆាប់[!?\s]*)+', 'ឆាប់! ', res)
    res = re.sub(r'\s+', ' ', res).strip()

    # Determine sentence-ending punctuation based on intent
    has_question = any(q in res for q in ['?', '？', 'មែនទេ', 'ស្អី', 'អ្វី', 'នរណា', 'អ្នកណា', 'ម៉េច', 'យ៉ាងម៉េច', 'រឿងអី', 'ឯណា', 'កាលណា', 'ប៉ុន្មាន'])
    if has_question:
        if '!' in res:
            res = re.sub(r'[!?។.\s]+$', '?!', res)
        else:
            res = re.sub(r'[!?។.\s]+$', '?', res)
    else:
        if any(w in res for w in ['!', '！', 'ភ្លាម', 'ឆាប់', 'ឈប់', 'រត់', 'កុំ', 'ជួយ', 'ហ៊ាន', 'ងាប់', 'សម្លាប់', 'បិទមាត់']):
            res = re.sub(r'[!?។.\s]+$', '!', res)
        else:
            res = re.sub(r'[!?។.\s]+$', '។', res)

    # 4. Semantic matching for boss/knowledge
    if re.search(r'ខ្ញុំ.*(?:ចៅហ្វាយ|ថៅកែ)', res):
        return 'ខ្ញុំនេះទើបជាថៅកែពិតប្រាកដ!'
    if re.search(r'ខ្ញុំ.*ដឹង', res) and len(res) <= 15:
        return 'ខ្ញុំដឹងតាំងពីដំបូងមកម្ល៉េះ!'

    # 5. Lip-Sync & Script Adaptation: Match duration strictly!
    # If duration_sec <= 1.2s or original text was <=3 characters, keep strictly concise so audio never overruns mouth closing!
    is_short = (duration_sec is not None and duration_sec <= 1.2) or (zh_text and len(zh_text.strip()) <= 3)

    if is_short:
        if "បាទ" in res:
            res = "បាទ!"
        elif "ចាស" in res:
            res = "ចាស!"
        elif "មិនអី" in res:
            res = "មិនអីទេ!"
        elif "ឈប់" in res:
            res = "ឈប់!"
        elif "ចេញ" in res:
            res = "ចេញទៅ!"
        elif "រត់" in res:
            res = "រត់ទៅ!"
        elif "លឿន" in res or "ឆាប់" in res:
            res = "ឆាប់ឡើង!"
        elif "ជួយ" in res:
            res = "ជួយផង!"
        elif "សុំទោស" in res:
            res = "សុំទោស!"
        elif "អរគុណ" in res:
            res = "អរគុណ!"
        elif "ស្អី" in res or "អ្វី" in res:
            res = "ស្អីគេ?!"
        elif "ម៉េច" in res:
            res = "ម៉េចចឹង?!"
        elif "ដឹង" in res:
            res = "ដឹងហើយ!"
    elif len(res) <= 12:
        if res.endswith("?!") or res.endswith("?"):
            if "ស្អី" in res or "អ្វី" in res:
                res = "ស្អីគេហ្នឹង?!"
            elif "ម៉េច" in res:
                res = "ម៉េចក៏បែបនេះ?!"
            elif "នរណា" in res or "អ្នកណា" in res:
                res = "តើនរណាគេ?!"
            elif "មែនទេ" in res:
                res = "ពិតមែនទេ?!"
        elif "បាទ" in res:
            res = "បាទ ខ្ញុំយល់ហើយ!"
        elif "ចាស" in res:
            res = "ចាស ខ្ញុំយល់ហើយ!"
        elif "មិនអី" in res:
            res = "មិនអីទេ កុំបារម្ភ!"
        elif "ឈប់" in res:
            res = "ឈប់ភ្លាម!"
        elif "ចេញ" in res:
            res = "ឆាប់ចេញទៅ!"
        elif "រត់" in res:
            res = "ឆាប់រត់ទៅ!"
        elif "លឿន" in res or "ឆាប់" in res:
            res = "ប្រញាប់ឡើង!"
        elif "ជួយ" in res:
            res = "ជួយផង!"
        elif "សុំទោស" in res:
            res = "ខ្ញុំសុំទោស!"
        elif "អរគុណ" in res:
            res = "អរគុណច្រើន!"

    # 6. Single Continuous Breath Flow (១ ដង្ហើមជាប់គ្នា):
    # Strip internal mid-sentence commas and pauses so speech flows in 1 uninterrupted breath
    res = re.sub(r'[,，、:：;；—–_~]+', ' ', res)
    res = re.sub(r'[（）\(\)\[\]{}"“\'”`]+', ' ', res)
    res = re.sub(r'\s*([!！?？។.])\s*', r'\1 ', res)
    res = re.sub(r'\s{2,}', ' ', res).strip()

    # 7. Advanced Phonetic Articulation & Spacing Pre-Processing:
    try:
        from tts_engine import prepare_khmer_phonetic_for_speech
        res = prepare_khmer_phonetic_for_speech(res)
    except Exception:
        pass

    return res.strip()


def resolve_dubbing_mode(target_voice_override: Optional[str] = None) -> Tuple[bool, str]:
    """
    Determine whether dubbing should be Multi-Voice or Single-Voice, and the chosen single voice.
    Defaults strictly to Single-Voice 'piseth' unless explicitly configured.
    """
    override_str = str(target_voice_override or "").lower().strip()
    if not override_str or override_str in ("auto", "none"):
        try:
            cfg_p = Path("data/story_config.json")
            if cfg_p.exists():
                with open(cfg_p, "r", encoding="utf-8") as f:
                    cfg_data = json.load(f)
                    if cfg_data.get("auto_multi_voice") or cfg_data.get("khmer_voice") == "multi":
                        override_str = "multi"
                    else:
                        override_str = cfg_data.get("khmer_voice", "piseth")
        except Exception:
            override_str = "piseth"

    if not override_str or override_str in ("auto", "none"):
        override_str = "piseth"

    is_multi = override_str in ("multi", "auto_multi")
    chosen_single_voice = "sreymom" if override_str in ("sreymom", "female", "ស្រីមុំ", "តួស្រី") else "piseth"
    return is_multi, chosen_single_voice


def infer_drama_persona_acoustics(
    item: Dict[str, Any],
    is_multi: bool = False,
    chosen_single_voice: str = "piseth"
) -> Dict[str, Any]:
    """
    Dynamically analyzes dialogue item to deduce persona role, vocal pitch (pitch_hz),
    speaking rate (rate_percent), and assign authentic character voice.
    - Single Voice Mode (is_multi=False): Strictly 1 single voice (Piseth Solo or Sreymom Solo),
      0 pitch shift, 0 rate shift. Every line is unified, natural, and consistent.
    - Multi-Voice Mode (is_multi=True): Sreymom for females, Piseth for males with persona modulation.
      Differentiates:
      - Heroine / Female Lead (ស្រីស្លូត/តួឯកស្រី e.g. 林早早): sreymom (+4Hz, +2%)
      - Villainess / Jealous Rival / Screaming Woman (ស្រីកំណាច/តួកាច/ឌឺដង e.g. 沈曼琳): sreymom (+18Hz, +15%)
      - Mother / Mother-in-Law / Elder Woman (ម្តាយក្មេក/លោកស្រី e.g. 婆婆): sreymom (-18Hz, -8%)
      - Hero / Male Lead / CEO (តួឯកប្រុស/លោកប្រធាន e.g. 李沐谦): piseth (-10Hz, +2%)
      - Angry Antagonist / Shouting Male (តួប្រុសខឹង/ឈ្លោះប្រកែក): piseth (+14Hz, +18%)
      - Elder Male / Grandfather / Butler (លោកតា/ឪពុក/មេផ្ទះ): piseth (-20Hz, -10%)
    """
    if not is_multi:
        v = "sreymom" if str(chosen_single_voice).lower() in ("sreymom", "female", "ស្រីមុំ", "តួស្រី") else "piseth"
        v_desc = "ស្រីមុំ (Sreymom Solo)" if v == "sreymom" else "ពិសិដ្ឋ (Piseth Solo)"
        return {
            "voice": v,
            "pitch_hz": 0,
            "rate_percent": 0,
            "speaker": v_desc
        }
    orig_text = str(item.get("text_original") or item.get("text") or "").strip()
    km_text = str(item.get("text_km") or "").strip()
    speaker_raw = str(item.get("speaker") or item.get("speaker_role") or "").lower()
    role_hint = str(item.get("detected_role") or item.get("role") or "").lower()

    # Pre-existing values if already provided
    try:
        pitch = int(item.get("pitch_hz", 0))
    except Exception:
        pitch = 0
    try:
        rate = int(item.get("rate_percent", 0))
    except Exception:
        rate = 0

    # 1. Mother-in-law / Elder Woman
    elder_female_zh = ["妈", "婆婆", "老夫人", "伯母", "母亲", "奶奶", "夫人", "李夫人"]
    elder_female_km = ["ម៉ាក់ក្មេក", "ម្តាយក្មេក", "អ្នកម៉ាក់", "លោកយាយ", "ម៉ាក់", "លោកស្រី"]
    is_elder_female = any(k in orig_text for k in elder_female_zh) or any(k in km_text for k in elder_female_km) or "mother" in speaker_raw or "婆" in speaker_raw or "ម្តាយ" in speaker_raw or "elder_female" in role_hint

    # 2. Grandfather / Elder Male
    elder_male_zh = ["爷爷", "老太爷", "父亲", "伯父", "老头", "管家", "老爷"]
    elder_male_km = ["លោកតា", "លោកប៉ា", "ឪពុក", "លោកអ៊ំ", "លោកមេផ្ទះ"]
    is_elder_male = any(k in orig_text for k in elder_male_zh) or any(k in km_text for k in elder_male_km) or "grandpa" in speaker_raw or "father" in speaker_raw or "លោកតា" in speaker_raw or "elder_male" in role_hint

    # 3. Villainess / Mean Sister / Screaming / Mocking Woman
    villainess_zh = ["白痴", "贱人", "你敢", "滚", "算什么东西", "要脸不要", "狐狸精", "死丫头", "不要脸", "沈曼琳", "小三", "给脸不要脸", "野种", "狐媚子", "看你脸"]
    villainess_km = ["អាចង្រៃ", "ស្រីឆ្កួត", "មីក្បត់", "ឆ្កួតមែន", "មុខក្រាស់", "ឯងគិតថាឯងជាស្អី", "ចេញទៅ!", "ល្ងង់", "ស្រីថោកទាប", "ស្រីក្បត់", "មុខល្ងង់", "ស៊ិន ម៉ាន់លីន", "沈曼琳"]
    is_villainess = any(k in orig_text for k in villainess_zh) or any(k in km_text for k in villainess_km) or "villainess" in speaker_raw or "曼琳" in speaker_raw or "តួកាច" in speaker_raw

    # 4. Female Lead / Suffering / Sweet / Crying
    heroine_zh = ["早早", "林早早", "求求你", "为什么", "放过我", "呜呜", "对不起", "孩子", "肚子", "求你"]
    heroine_km = ["លីន ចាវចាវ", "សូមអង្វរ", "ហេតុអ្វី", "អត់ទោស", "សុំទោស", "កូនរបស់ខ្ញុំ", "កូនក្នុងពោះ", "អាណិតខ្ញុំផង"]
    is_heroine = any(k in orig_text for k in heroine_zh) or any(k in km_text for k in heroine_km) or "heroine" in speaker_raw or "早早" in speaker_raw or "តួឯកស្រី" in speaker_raw

    # 5. Angry Male / Shouting / Fight
    angry_male_zh = ["混蛋", "找死", "闭嘴", "给我滚", "废话", "弄死你", "混账", "住口", "你找死"]
    angry_male_km = ["បិទមាត់!", "អាគម្រក់!", "ឯងចង់ងាប់មែនទេ!", "ចេញទៅ!", "ឈប់ភ្លាម!", "កុំមកចង់ខ្លាំង!", "ចង់ងាប់"]
    is_angry_male = any(k in orig_text for k in angry_male_zh) or any(k in km_text for k in angry_male_km) or ("!" in orig_text and ("男" in speaker_raw or "male" in speaker_raw or "piseth" in speaker_raw))

    # 6. Male Lead / CEO / President
    male_lead_zh = ["李沐谦", "李总", "少爷", "少东家", "顾总", "先生", "总裁", "沐谦", "张昭"]
    male_lead_km = ["លោកប្រធាន", "លី មូឈាន", "ចៅហ្វាយ", "ប្តីសម្លាញ់", "លោកម្ចាស់", "ចាងចាវ", "ចាង ចាវ"]
    is_male_lead = any(k in orig_text for k in male_lead_zh) or any(k in km_text for k in male_lead_km) or "ceo" in speaker_raw or "沐谦" in speaker_raw or "តួឯកប្រុស" in speaker_raw

    # Determine gender if multi-voice
    curr_voice = str(item.get("voice", "")).lower()
    if not is_multi:
        assigned_voice = chosen_single_voice
    else:
        if curr_voice in ("piseth", "sreymom"):
            assigned_voice = curr_voice
        elif is_elder_female or is_villainess or is_heroine or "female" in speaker_raw or "sreymom" in speaker_raw or "ស្រី" in speaker_raw or "早早" in orig_text or "曼琳" in orig_text:
            assigned_voice = "sreymom"
        elif is_elder_male or is_angry_male or is_male_lead or "male" in speaker_raw.replace("female", "") or "piseth" in speaker_raw or "ប្រុស" in speaker_raw or "沐谦" in orig_text or "张昭" in orig_text:
            assigned_voice = "piseth"
        else:
            assigned_voice = "sreymom" if role_hint == "female" else "piseth"

    # Dynamic Acoustic Persona Assignment
    if pitch == 0 and rate == 0:
        if assigned_voice == "sreymom":
            if is_villainess:
                pitch = 18
                rate = 15
                speaker_desc = "ស្រីមុំ (Sreymom - តួកាច/ឌឺដង)"
            elif is_elder_female:
                pitch = -18
                rate = -8
                speaker_desc = "ស្រីមុំ (Sreymom - ម្តាយក្មេក/លោកស្រី)"
            elif is_heroine:
                pitch = 4
                rate = 2
                speaker_desc = "ស្រីមុំ (Sreymom - តួឯកស្រីស្លូត)"
            else:
                pitch = 2
                rate = 4
                speaker_desc = "ស្រីមុំ (Sreymom - តួស្រី)"
        else:  # piseth
            if is_angry_male:
                pitch = 14
                rate = 18
                speaker_desc = "ពិសិដ្ឋ (Piseth - តួប្រុសខឹង)"
            elif is_elder_male:
                pitch = -20
                rate = -10
                speaker_desc = "ពិសិដ្ឋ (Piseth - លោកតា/ចាស់ទុំ)"
            elif is_male_lead:
                pitch = -10
                rate = 2
                speaker_desc = "ពិសិដ្ឋ (Piseth - តួឯកប្រុស/លោកប្រធាន)"
            else:
                pitch = -2
                rate = 2
                speaker_desc = "ពិសិដ្ឋ (Piseth - តួប្រុស)"

        # In Single Voice Mode: apply cross-gender pitch modulation
        if not is_multi:
            if chosen_single_voice == "piseth":
                if is_elder_female:
                    pitch = -12
                    rate = -8
                    speaker_desc = "ពិសិដ្ឋ (Piseth - ម្តាយក្មេក)"
                elif is_villainess or is_heroine or "female" in speaker_raw or "ស្រី" in speaker_raw:
                    pitch = 28
                    rate = 6
                    speaker_desc = "ពិសិដ្ឋ (Piseth - បញ្ចូលសំឡេងតួស្រី)"
            elif chosen_single_voice == "sreymom":
                if is_elder_male:
                    pitch = -26
                    rate = -10
                    speaker_desc = "ស្រីមុំ (Sreymom - លោកតា/ចាស់ទុំ)"
                elif is_angry_male or is_male_lead or "male" in speaker_raw.replace("female", "") or "ប្រុស" in speaker_raw:
                    pitch = -24
                    rate = -4
                    speaker_desc = "ស្រីមុំ (Sreymom - បញ្ចូលសំឡេងតួប្រុស)"
    else:
        pitch = max(-35, min(35, pitch))
        rate = max(-20, min(30, rate))
        speaker_desc = item.get("speaker") or ("ស្រីមុំ (Sreymom)" if assigned_voice == "sreymom" else "ពិសិដ្ឋ (Piseth)")

    return {
        "voice": assigned_voice,
        "pitch_hz": pitch,
        "rate_percent": rate,
        "speaker": speaker_desc
    }


class DramaTranslator:
    def __init__(self, gemini_api_key: Optional[str] = None, groq_api_key: Optional[str] = None):
        self.api_keys: List[str] = []
        self.clients: List[Any] = []
        self.current_key_idx = 0
        self.groq_keys: List[str] = []
        self.current_groq_idx = 0
        self.groq_api_key = groq_api_key or os.environ.get("GROQ_API_KEY", "")
        self._shared_http_client: Optional[httpx.AsyncClient] = None

        # Load config from file if present
        cfg = self._load_ai_config()
        if not self.groq_api_key and cfg.get("groq_api_key"):
            self.groq_api_key = cfg.get("groq_api_key", "").strip()

        groq_pool = cfg.get("groq_keys") or []
        if isinstance(groq_pool, list) and groq_pool:
            self.groq_keys = [k.strip() for k in groq_pool if k and str(k).startswith("gsk_")]
        if self.groq_api_key and self.groq_api_key not in self.groq_keys:
            self.groq_keys.insert(0, self.groq_api_key)
        if self.groq_keys and not self.groq_api_key:
            self.groq_api_key = self.groq_keys[0]

        raw_key = gemini_api_key or cfg.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY", "")
        if not raw_key and cfg.get("keys"):
            raw_key = "\n".join(cfg.get("keys", []))
        if raw_key:
            keys = [k.strip() for k in str(raw_key).replace(",", "\n").splitlines() if k.strip()]
            self.set_api_keys(keys)
        else:
            self.api_key = ""
            self.client = None

    def get_active_groq_key(self) -> str:
        if not self.groq_keys:
            return self.groq_api_key
        return self.groq_keys[self.current_groq_idx % len(self.groq_keys)]

    def rotate_groq_key(self) -> str:
        if not self.groq_keys:
            return self.groq_api_key
        self.current_groq_idx = (self.current_groq_idx + 1) % len(self.groq_keys)
        self.groq_api_key = self.groq_keys[self.current_groq_idx]
        return self.groq_api_key

    def _load_ai_config(self) -> Dict[str, Any]:
        try:
            cfg_p = Path("data/ai_provider_config.json")
            if cfg_p.exists():
                with open(cfg_p, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def get_http_client(self) -> httpx.AsyncClient:
        if self._shared_http_client is None or self._shared_http_client.is_closed:
            self._shared_http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(5.0, connect=3.0),
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=40),
                follow_redirects=True
            )
        return self._shared_http_client

    async def close(self):
        if self._shared_http_client and not self._shared_http_client.is_closed:
            await self._shared_http_client.aclose()

    def set_api_keys(self, keys: List[str]):
        clean_keys = [k.strip() for k in keys if k and k.strip()]
        self.api_keys = clean_keys
        self.api_key = clean_keys[0] if clean_keys else ""
        self.clients = []
        self.current_key_idx = 0
        if GENAI_AVAILABLE and clean_keys:
            for k in clean_keys:
                try:
                    c = genai.Client(api_key=k)
                    self.clients.append(c)
                except Exception as e:
                    print(f"Gemini client setup error for key: {e}")
        self.client = self.clients[0] if self.clients else None

    def set_api_key(self, api_key: str):
        self.set_api_keys([api_key] if api_key else [])

    def get_client(self) -> Optional[Any]:
        if not self.clients:
            return None
        c = self.clients[self.current_key_idx % len(self.clients)]
        self.current_key_idx = (self.current_key_idx + 1) % len(self.clients)
        return c

    def _pre_normalize_chinese(self, text: str) -> str:
        """Pre-normalize Chinese drama slang and idioms before machine translation."""
        res = text.strip()
        for pat, rep in CHINESE_DRAMA_PRE_NORM:
            res = re.sub(pat, rep, res)
        return res.strip()

    def _post_polish_khmer(self, km_text: str, zh_text: str = "", voice: str = "piseth") -> str:
        """Polish translated Khmer into lively Cambodian TV drama dubbing dialogue."""
        res = re.sub(r'[\s\u200b]+', ' ', km_text.strip()).strip()
        return enrich_khmer_drama_dialogue(res, zh_text, voice)

    async def translate_text_free(self, text: str, source_lang: str = "auto", voice: str = "piseth") -> str:
        """
        Ultra-fast, non-blocking free translation with connection pooling and 5-second timeout.
        """
        if not text or not text.strip():
            return ""

        cleaned = self._pre_normalize_chinese(text.strip())
        clean_key = re.sub(r'[\s!！?？,，.。~～`\'"]+', '', cleaned)
        custom_dict = load_drama_dictionary()
        if clean_key in custom_dict:
            return self._post_polish_khmer(custom_dict[clean_key], cleaned, voice)

        sl = "auto" if source_lang in ("auto", "", None) else source_lang
        if sl in ("zh", "chinese"):
            sl = "zh-CN"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Referer": "https://translate.google.com/"
        }

        client = self.get_http_client()

        # 1. Primary: Google Clients5 API
        try:
            url1 = "https://clients5.google.com/translate_a/t"
            params1 = {
                "client": "dict-chrome-ex",
                "sl": sl,
                "tl": "km",
                "q": cleaned
            }
            resp = await client.get(url1, params=params1, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    first = data[0]
                    if isinstance(first, list) and len(first) > 0:
                        trans = str(first[0]).strip()
                        if trans:
                            return self._post_polish_khmer(trans, cleaned, voice)
                    elif isinstance(first, str) and first.strip():
                        return self._post_polish_khmer(first.strip(), cleaned, voice)
        except Exception:
            pass

        # 2. Secondary: Google single endpoint
        try:
            url2 = "https://translate.googleapis.com/translate_a/single"
            params2 = {
                "client": "dict-chrome-ex",
                "sl": sl,
                "tl": "km",
                "dt": "t",
                "q": cleaned
            }
            resp = await client.get(url2, params=params2, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                    parts = [seg[0] for seg in data[0] if seg and len(seg) > 0 and seg[0]]
                    res = "".join(parts).strip()
                    if res:
                        return self._post_polish_khmer(res, cleaned, voice)
        except Exception:
            pass

        return self._post_polish_khmer(cleaned, cleaned, voice)

    def _determine_strictly_two_voices(
        self,
        item: Dict[str, Any],
        target_voice_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Assign voice, pitch, and speech rate with cinema drama persona modulation.
        Honors target_voice_override or defaults to multi-voice from data/story_config.json.
        """
        is_multi, chosen_single_voice = resolve_dubbing_mode(target_voice_override)
        persona = infer_drama_persona_acoustics(
            item,
            is_multi=is_multi,
            chosen_single_voice=chosen_single_voice
        )
        return {
            "voice": persona["voice"],
            "rate_percent": persona["rate_percent"],
            "pitch_hz": persona["pitch_hz"],
            "character_role": persona["speaker"]
        }

    async def translate_dialogues_groq(
        self,
        dialogues: List[Dict[str, Any]],
        mode: str = "drama_dubbing",
        source_lang: str = "auto",
        voice_directive: str = "",
        active_system_prompt: str = "",
        chosen_single_voice: str = "piseth",
        is_multi: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """Ultra-fast Qwen-3.8-27b / GPT-OSS-120b / Llama via Groq Cloud API for cinematic Khmer dubbing."""
        active_key = self.get_active_groq_key()
        if not active_key or not str(active_key).startswith("gsk_"):
            return None

        client = self.get_http_client()
        chunk_size = 25
        all_results = []
        candidate_models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]

        for i in range(0, len(dialogues), chunk_size):
            chunk = dialogues[i:i + chunk_size]
            enriched_chunk = []
            for itm in chunk:
                c_itm = dict(itm)
                s = float(c_itm.get("start", 0.0))
                e = float(c_itm.get("end", s + 2.0))
                c_itm["duration"] = round(max(0.2, e - s), 2)
                enriched_chunk.append(c_itm)

            prompt = f"""Mode: {mode} (Authentic Cambodian TV Drama Dubbing)
Source Language: {source_lang}
Input script items in JSON (includes exact 'duration' in seconds):
{json.dumps(enriched_chunk, ensure_ascii=False, indent=2)}

Translate each dialogue item into emotional, natural spoken Khmer dubbing script ('text_km').
{voice_directive}
CRITICAL LIP-SYNC & SCRIPT DURATION ADAPTATION:
- Match the spoken duration of 'text_km' to the item's duration.
- For short lines (duration <= 1.2s or short words like 滚, 走, 站住, 住手, 救命, 闭嘴): translate into 1-3 PUNCHY words (e.g. "ចេញទៅ!", "ឈប់ភ្លាម!", "ទៅ!", "ជួយផង!", "បិទមាត់!"). NEVER expand short shouts into long explanations, so speech finishes when the mouth closes.
- For longer lines (duration >= 3.0s): translate with natural dramatic cadence.
Return JSON object with key "dialogues" containing an array with keys: id, start, end, text_original, text_km, speaker, voice, rate_percent, pitch_hz, emotion."""

            chunk_success = False
            for model_name in candidate_models:
                cur_key = self.get_active_groq_key()
                headers = {
                    "Authorization": f"Bearer {cur_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": active_system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.3
                }
                try:
                    resp = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                    if resp.status_code == 200:
                        r_data = resp.json()
                        content = r_data["choices"][0]["message"]["content"]
                        parsed = json.loads(content)
                        items = parsed if isinstance(parsed, list) else parsed.get("dialogues") or parsed.get("items") or list(parsed.values())[0]
                        if isinstance(items, list):
                            for j, item in enumerate(items):
                                if j < len(chunk):
                                    item["start"] = chunk[j].get("start", item.get("start", 0))
                                    item["end"] = chunk[j].get("end", item.get("end", 0))
                                    orig_line = chunk[j].get("text_original", chunk[j].get("text", ""))
                                    item["text_original"] = orig_line

                                    # Infer acoustic persona, voice, pitch, and rate
                                    persona = infer_drama_persona_acoustics(
                                        item,
                                        is_multi=is_multi,
                                        chosen_single_voice=chosen_single_voice
                                    )
                                    v = persona["voice"]
                                    item["voice"] = v
                                    item["pitch_hz"] = persona["pitch_hz"]
                                    item["rate_percent"] = persona["rate_percent"]
                                    item["speaker"] = persona["speaker"]
                                    if not is_multi:
                                        item["voice"] = chosen_single_voice
                                        item["pitch_hz"] = 0
                                        item["rate_percent"] = 0
                                        item["speaker"] = "ស្រីមុំ (Sreymom Solo)" if chosen_single_voice == "sreymom" else "ពិសិដ្ឋ (Piseth Solo)"
                                    
                                    dur_sec = round(max(0.2, float(item["end"]) - float(item["start"])), 2)
                                    item["text_km"] = enrich_khmer_drama_dialogue(
                                        item.get("text_km", ""),
                                        orig_line,
                                        item["voice"],
                                        duration_sec=dur_sec
                                    )
                            all_results.extend(items)
                            chunk_success = True
                            break
                    elif resp.status_code == 429:
                        # Rotate to next key in key pool
                        self.rotate_groq_key()
                        continue
                    elif resp.status_code == 404:
                        # Model not available, try next model
                        continue
                except Exception as e:
                    print(f"Groq API call note ({model_name}): {e}")
                    continue

            if not chunk_success:
                break

        if len(all_results) == len(dialogues):
            return all_results
        return None

    async def translate_dialogues(
        self,
        dialogues: List[Dict[str, Any]],
        mode: str = "drama_dubbing",
        source_lang: str = "auto",
        target_voice_override: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Translate dialogue items into authentic Khmer drama dubbing lines.
        Multi-voice with character persona pitch & rate differentiation is fully enabled by default.
        """
        if not dialogues:
            return []

        # Determine Single Voice vs Multi-Voice mode
        is_multi, chosen_single_voice = resolve_dubbing_mode(target_voice_override)

        if not is_multi:
            voice_directive = f"Single Voice Dubbing Mode: Assign 'voice' strictly to '{chosen_single_voice}' for ALL lines with pitch_hz: 0 and rate_percent: 0. Style: Professional Cambodian television drama solo narrator (អ្នកបញ្ចូលសំឡេងទោលតែម្នាក់គត់) speaking clearly, naturally, and in 1 continuous breath per sentence."
            active_system_prompt = DRAMA_PROMPT_SINGLE_VOICE.replace("{VOICE}", chosen_single_voice)
        else:
            voice_directive = "Dual Character Voice Dubbing Mode: Assign 'voice' strictly to 'sreymom' (female) or 'piseth' (male). Differentiate characters with pitch_hz and rate_percent: Villainess (+18Hz, +15%), Mother-in-law (-18Hz, -8%), Female Lead (+4Hz, +2%), Male Lead (-10Hz, +2%), Angry Male (+14Hz, +18%), Elder Male (-20Hz, -10%)."
            active_system_prompt = DRAMA_PROMPT_SYSTEM

        # Inject Custom Drama Dictionary & Glossary terms into prompt
        custom_dict = load_drama_dictionary()
        if custom_dict:
            dict_str = ", ".join([f"'{k}' ➔ '{v}'" for k, v in custom_dict.items()])
            glossary_block = f"\n\nSTRICT CHARACTER NAMES & VOCABULARY DICTIONARY (You MUST use these exact Khmer terms for translation):\n{dict_str}\n"
            active_system_prompt = active_system_prompt + glossary_block

        # 1. Groq Ultra-Fast AI (77 Keys Pool)
        if self.groq_api_key and str(self.groq_api_key).startswith("gsk_"):
            try:
                groq_res = await self.translate_dialogues_groq(
                    dialogues=dialogues,
                    mode=mode,
                    source_lang=source_lang,
                    voice_directive=voice_directive,
                    active_system_prompt=active_system_prompt,
                    chosen_single_voice=chosen_single_voice,
                    is_multi=is_multi
                )
                if groq_res:
                    return groq_res
            except Exception as ge:
                print(f"Groq translation warning: {ge}")

        # 2. Gemini AI Studio Translation (Only run if key starts with AIzaSy)
        valid_gemini_keys = [k for k in self.api_keys if k.startswith("AIzaSy")]
        if self.clients and valid_gemini_keys:
            try:
                chunk_size = 18
                for i in range(0, len(dialogues), chunk_size):
                    chunk = dialogues[i:i + chunk_size]
                    enriched_chunk = []
                    for itm in chunk:
                        c_itm = dict(itm)
                        s = float(c_itm.get("start", 0.0))
                        e = float(c_itm.get("end", s + 2.0))
                        c_itm["duration"] = round(max(0.2, e - s), 2)
                        enriched_chunk.append(c_itm)

                    prompt = f"""Mode: {mode} (Authentic Cambodian TV Drama Dubbing)
Source Language: {source_lang}
Input script items in JSON (includes exact 'duration' in seconds):
{json.dumps(enriched_chunk, ensure_ascii=False, indent=2)}

Translate each dialogue item into emotional, natural spoken Khmer dubbing script ('text_km').
{voice_directive}
CRITICAL LIP-SYNC & SCRIPT DURATION ADAPTATION:
- Match the spoken duration of 'text_km' to the item's duration.
- For short lines (duration <= 1.2s or short words like 滚, 走, 站住, 住手, 救命, 闭嘴): translate into 1-3 PUNCHY words (e.g. "ចេញទៅ!", "ឈប់ភ្លាម!", "ទៅ!", "ជួយផង!", "បិទមាត់!"). NEVER expand short shouts into long explanations, so speech finishes when the mouth closes.
- For longer lines (duration >= 3.0s): translate with natural dramatic cadence.
Return ONLY valid JSON array with keys: id, start, end, text_original, text_km, speaker, voice, rate_percent, pitch_hz, emotion."""

                    active_client = self.get_client() or self.client
                    def _call_gemini(c):
                        return c.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                system_instruction=active_system_prompt,
                                response_mime_type="application/json"
                            )
                        )

                    try:
                        response = await asyncio.wait_for(asyncio.to_thread(_call_gemini, active_client), timeout=12.0)
                    except Exception as call_err:
                        print(f"Gemini key error, retrying next key in pool: {call_err}")
                        alt_client = self.get_client()
                        if alt_client and alt_client != active_client:
                            try:
                                response = await asyncio.wait_for(asyncio.to_thread(_call_gemini, alt_client), timeout=12.0)
                            except Exception:
                                break
                        else:
                            break
                    if response.text:
                        parsed = json.loads(response.text)
                        if isinstance(parsed, list):
                            for j, item in enumerate(parsed):
                                if j < len(chunk):
                                    item["start"] = chunk[j].get("start", item.get("start", 0))
                                    item["end"] = chunk[j].get("end", item.get("end", 0))
                                    orig_line = chunk[j].get("text_original", chunk[j].get("text", ""))
                                    item["text_original"] = orig_line

                                    persona = infer_drama_persona_acoustics(
                                        item,
                                        is_multi=is_multi,
                                        chosen_single_voice=chosen_single_voice
                                    )
                                    v = persona["voice"]
                                    item["voice"] = v
                                    item["pitch_hz"] = persona["pitch_hz"]
                                    item["rate_percent"] = persona["rate_percent"]
                                    item["speaker"] = persona["speaker"]
                                    if not is_multi:
                                        item["voice"] = chosen_single_voice
                                        item["pitch_hz"] = 0
                                        item["rate_percent"] = 0
                                        item["speaker"] = "ស្រីមុំ (Sreymom Solo)" if chosen_single_voice == "sreymom" else "ពិសិដ្ឋ (Piseth Solo)"
                                    
                                    dur_sec = round(max(0.2, float(item["end"]) - float(item["start"])), 2)
                                    item["text_km"] = enrich_khmer_drama_dialogue(
                                        item.get("text_km", ""),
                                        orig_line,
                                        item["voice"],
                                        duration_sec=dur_sec
                                    )
                                    if response and response.text:
                                        break
                                except Exception:
                                    pass
                            break

                    if response and response.text:
                        try:
                            clean_json = response.text.strip()
                            clean_json = re.sub(r'^```(?:json)?\s*', '', clean_json, flags=re.IGNORECASE)
                            clean_json = re.sub(r'\s*```$', '', clean_json)
                            parsed = json.loads(clean_json)
                            if isinstance(parsed, list):
                                for j, p_item in enumerate(parsed):
                                    global_idx = i + j
                                    if global_idx < len(dialogues):
                                        orig_item = dialogues[global_idx]
                                        p_item["id"] = orig_item.get("id", global_idx + 1)
                                        p_item["start"] = orig_item.get("start", p_item.get("start", 0))
                                        p_item["end"] = orig_item.get("end", p_item.get("end", 0))
                                        p_item["rate_percent"] = 0
                                        p_item["pitch_hz"] = 0
                                        v = target_voice_override or p_item.get("voice", orig_item.get("voice", "piseth"))
                                        p_item["voice"] = v
                                        p_item["text_km"] = enrich_khmer_drama_dialogue(
                                            p_item.get("text_km", ""),
                                            orig_item.get("text_original", ""),
                                            v
                                        )
                                        translated_items[global_idx] = p_item
                        except Exception as parse_err:
                            print(f"Gemini chunk parse error: {parse_err}")
            except Exception as e:
                print(f"Gemini batch translation note: {e}")

        # 3. High-Speed Local Drama Dubbing Engine (Concurrent with Semaphore=12 & Connection Pool)
        sem = asyncio.Semaphore(12)

        async def _translate_single(item: Dict[str, Any], idx: int) -> Dict[str, Any]:
            async with sem:
                orig_text = item.get("text") or item.get("text_original", "")
                start = item.get("start", 0.0)
                end = item.get("end", 0.0)
                dur_sec = round(max(0.2, end - start), 2)

                # Determine character role, voice, pitch, and rate
                v_info = self._determine_strictly_two_voices(item, target_voice_override)
                chosen_voice = v_info["voice"]

                    # Translate with drama pre-norm, post-polish, and dialogue enrichment
                    try:
                        text_km = await self.translate_text_free(
                            orig_text,
                            source_lang=source_lang,
                            voice=chosen_voice
                        )
                    except Exception as e:
                        print(f"Fallback translation error on line {global_idx}: {e}")
                        text_km = orig_text

                # Final pass enrichment: duration-aware script adaptation
                final_text_km = enrich_khmer_drama_dialogue(
                    text_km,
                    orig_text,
                    chosen_voice,
                    duration_sec=dur_sec
                )

                    return global_idx, {
                        "id": item.get("id", global_idx + 1),
                        "start": start,
                        "end": end,
                        "speaker": v_info["character_role"],
                        "text_original": orig_text,
                        "text_km": final_text_km,
                        "voice": chosen_voice,
                        "rate_percent": 0,
                        "pitch_hz": 0
                    }

            tasks = [_translate_single(idx) for idx in missing_indices]
            fallback_results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in fallback_results:
                if isinstance(res, tuple) and len(res) == 2:
                    g_idx, res_item = res
                    translated_items[g_idx] = res_item

        # 3. Final safety net: Ensure absolutely every dialogue has a valid item
        ordered_results = []
        for i in range(len(dialogues)):
            if i in translated_items:
                ordered_results.append(translated_items[i])
            else:
                orig_item = dialogues[i]
                orig_text = orig_item.get("text") or orig_item.get("text_original", "")
                v_info = self._determine_strictly_two_voices(orig_item, target_voice_override)
                ordered_results.append({
                    "id": orig_item.get("id", i + 1),
                    "start": orig_item.get("start", 0.0),
                    "end": orig_item.get("end", 0.0),
                    "speaker": v_info["character_role"],
                    "text_original": orig_text,
                    "text_km": final_text_km,
                    "voice": chosen_voice,
                    "rate_percent": v_info["rate_percent"],
                    "pitch_hz": v_info["pitch_hz"]
                }

        return ordered_results


def parse_srt_content(srt_text: str) -> List[Dict[str, Any]]:
    """Parse SRT subtitle text into dialogue objects with start/end in seconds."""
    items = []
    blocks = re.split(r'\n\s*\n', srt_text.strip())
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            idx = lines[0].strip()
            time_match = re.search(r'(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})', lines[1])
            if time_match:
                h1, m1, s1, ms1, h2, m2, s2, ms2 = [int(x) for x in time_match.groups()]
                start_sec = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000.0
                end_sec = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000.0
                text = " ".join([l.strip() for l in lines[2:] if l.strip()])

                speaker = "Narrator"
                speaker_match = re.match(r'^\[?([A-Za-z0-9_\u1780-\u17FF\s]+)\]?:\s*(.*)', text)
                if speaker_match:
                    speaker = speaker_match.group(1).strip()
                    text = speaker_match.group(2).strip()

                items.append({
                    "id": idx,
                    "start": round(start_sec, 2),
                    "end": round(end_sec, 2),
                    "speaker": speaker,
                    "text": text,
                    "text_original": text
                })
    return items


def format_srt_content(dialogues: List[Dict[str, Any]], use_km: bool = True) -> str:
    """Export dialogues to standard SRT subtitle string."""
    def _sec_to_srt_time(sec: float) -> str:
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = int(sec % 60)
        ms = int(round((sec - int(sec)) * 1000))
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    lines = []
    for idx, item in enumerate(dialogues, start=1):
        start_str = _sec_to_srt_time(item.get("start", 0))
        end_str = _sec_to_srt_time(item.get("end", 0))
        text = item.get("text_km") if use_km else item.get("text_original", item.get("text", ""))
        lines.append(f"{idx}\n{start_str} --> {end_str}\n{text}\n")

    return "\n".join(lines)
