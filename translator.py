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
Translate dialogue lines into natural, emotional, authentic spoken Khmer film dubbing language (ភាសាបញ្ចូលសំឡេងរឿងភាគទូរទស្សន៍ខ្មែរ).

STRICT Voice Rules:
- There are ONLY TWO voices:
  1. 'piseth' for ALL Male characters (Male Lead, Father, Brother, Officers, Male Supporting).
  2. 'sreymom' for ALL Female characters (Female Lead, Mother, Sister, Mistress, Female Supporting).
- NEVER alter pitch or rate. Both voices must be clean, natural, and standard: rate_percent=0, pitch_hz=0.

Key Film Phrasing:
- Use natural spoken film vocabulary (e.g., "ឯងចង់ធ្វើស្អីហ្នឹង?!", "ហ៊ានប៉ះមនុស្សរបស់ខ្ញុំផង ឯងខ្វាក់ភ្នែកហើយមែនទេ?!", "បិទមាត់ភ្លាម!", "កុំនិយាយច្រើនពេក!").
- Output valid JSON array with keys: id, start, end, text_original, text_km, speaker, voice, rate_percent, pitch_hz.
"""

# Pre-normalization: normalize Chinese drama slang, spoken colloquialisms, and common whisper misrecognitions
CHINESE_DRAMA_PRE_NORM = [
    # Curses, exclamations & common drama slangs
    (r'[幹操草][\s，,]*[動动]了.*', '动了！有动静了！'),
    (r'[幹操草][\s，,]*', ''),
    (r'敦仁', ''),
    (r'送你回去', '陪你回家'),
    (r'送你走', '带你离开'),
    (r'送你', '陪你'),
    (r'送什么', '到底要送去哪里啊，我哪里都不去！'),
    (r'跟[你您]送', '提醒你'),
    (r'^(?:快)?走[!！。]?$', '快点离开这里！'),
    (r'^走吧[!！。]?$', '我们快走吧！'),
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
    (r'曹早', '曹早！快点过来'),
    (r'想得美', '别白日做梦了'),
    (r'放肆', '放肆！胆大包天'),
    (r'住手', '立刻住手'),
    (r'救命', '快救命啊'),
    (r'閉嘴|闭嘴', '立刻闭嘴！别废话'),
    (r'滾|滚', '立刻给我滚出去'),
    (r'憑什麼|凭话', '你凭什么这么做'),
    (r'等著瞧|等着瞧', '你给我等着瞧'),
    (r'聽到了嗎|听到了吗', '听清楚了没有'),
    (r'別碰我|别碰我', '别碰我！放开我'),
    (r'放開我|放开我', '快放开我'),
    (r'怎麼可能|怎么可能', '这绝不可能'),
    (r'真的嗎|真的吗', '这是真的吗'),
    (r'胡說八道', '全是胡说八道'),
    (r'少廢話|少废话', '少废话！快照做'),
    (r'算了吧', '就到此为止吧'),
    (r'對不起|对不起', '我真的很对不起'),
    (r'我錯了|我错了', '我知道错了'),
    (r'帶走|带走', '把人带走'),
    (r'站住', '站住！别跑'),
    (r'你敢', '你敢动一下试试'),
    (r'誰啊|谁啊', '到底是谁啊'),
    (r'怎麼辦|怎么办', '现在该怎么办啊'),
    (r'你在[幹干]什麼|你在[幹干]什么|[幹干]什麼|[幹干]什么', '你到底在干什么啊'),
    (r'在哪[裡里]|在哪里', '到底在哪里啊'),
    (r'快[點点]|快点', '快点！快抓紧时间'),
    (r'等等我', '等等我！先别走'),
    (r'禮幕前|礼幕前|李幕千', '李慕千'),
    (r'伯儿|伯兒', '伯父'),

    # Modern TV Drama & Workplace/CEO Specific Misrecognitions & Idioms
    (r'什么林|什么李|什么王|什么张', '到底是哪个姓林的！'),
    (r'晚充自己|冒充自己', '假冒豪门少爷身份！'),
    (r'坏了云京集团老板的孩子|怀了云京集团老板的孩子', '怀了云京集团董事长的亲生骨肉！'),
    (r'公司总[住助]|总助', '董事长特别助理'),
    (r'开[出除]我的全[县权]', '开除我的全部权力！'),
    (r'我家的英文|家里[的在]英文|英处里', '我们豪门家族内部的私事'),
    (r'死不了资助', '我给你家的巨额资助'),
    (r'甘歉|买电话', '打电话叫人过来'),
    (r'这些幽知俗口', '少在这胡说八道！'),
    (r'开放想 够有个老公', '你根本不配做她的丈夫！'),
    (r'无数的见题', '成天惹出这些是非'),
    (r'尊敬礼物', '不知好歹的家伙！'),
    (r'有把你打出公司|打出公司', '把你从公司彻底开除轰出去！'),
    (r'老板轻轻出手的所认', '老板绝不会轻易饶过你！'),
    (r'尽过才无落赖', '到那时候你后悔都来不及了！'),
    (r'早早那边好像遇到麻烦了', '早早那边好像遇到大麻烦了！'),
    (r'帮我去看[一遇遍眼]', '赶快帮我过去看一眼！'),
    (r'我实在是放弃[一不]下', '我心里实在放不下！'),
    (r'我这边[会不能][摸无]塞的', '我这边立刻过去处理！'),
    (r'那儿子你放心吧', '儿子你就放一百个心吧！'),
    (r'妈不会[让上]早早[受说]委屈的', '妈绝对不会让早早受半点委屈的！'),
    (r'慢点来电话了', '又有电话打进来了！'),
    (r'您您先挂[了個个]吧', '妈您先挂断电话吧！'),
    (r'你怀着孩子呢', '你现在怀着身孕呢！'),
    (r'有空了就回家', '有时间一定要多回趟家！'),
    (r'回家吃饭|吃饭啊', '回家吃顿热饭吧！'),
    (r'我等汤|给你等汤|炖汤', '我给你煲好了热汤等着你呢！'),
    (r'放心吧 阿姨|放心吧阿姨', '阿姨您就放心吧，我没事的！'),
    (r'我在公司被人欺[负負]了', '阿姨，我在公司被人故意欺负了！'),
    (r'[能我]不能开除的吗|我都开除了吗', '这种目中无人的人难道不能开除吗？！'),
    (r'别都不要|别动了', '立刻给我住手，别乱动！'),
    (r'钱老板.*陪不见', '就算钱老板来了也保不住你！'),

    # High-stakes Drama Tropes (Ancient & Modern)
    (r'小瘪三|穷屌丝|乡巴佬', '不知死活的穷小子'),
    (r'扫地出门', '彻底赶出家门！'),
    (r'断绝父子关系|断绝母子关系', '彻底断绝一切关系！'),
    (r'下跪求饶|下跪道歉', '立刻给我跪下求饶！'),
    (r'死到临头', '死到临头了还嘴硬！'),
    (r'不知天高地厚', '简直是不知天高地厚！'),
    (r'狗眼看人低', '真是狗眼看人低！')
]

# Post-translation polish: convert machine-translated Khmer into natural Khmer TV Drama Dubbing
KHMER_DUBBING_POST_CLEANUP = [
    # 1. Expand truncated dry words into expressive drama lines (បំបាត់ពាក្យខ្លីៗកំបុត)
    (r'^ដើរ[។!.]*$', 'ឆាប់ចេញទៅ! ប្រញាប់ឡើង!'),
    (r'^(?:ឆាប់)?ដើរទៅ[។!.]*$', 'ឆាប់ចេញពីទីនេះភ្លាមទៅ!'),
    (r'^ល្អ[។!.]*$', 'បានហើយ យល់ព្រម!'),
    (r'^បាទ[។!.]*$', 'បាទ ខ្ញុំយល់ហើយ!'),
    (r'^ចាស[។!.]*$', 'ចាស ខ្ញុំយល់ហើយ!'),
    (r'^ទេ[។!.]*$', 'អត់ទេ! មិនអាចជាដាច់ខាត!'),
    (r'^ឈប់[។!.]*$', 'ឈប់ភ្លាម! កុំរើឱ្យសោះ!'),
    (r'^លឿន[។!.]*$', 'ឆាប់ឡើង! ប្រញាប់បន្តិចទៅ!'),
    (r'^ប្រយ័ត្ន[។!.]*$', 'ប្រយ័ត្នខ្លួនណា!'),
    (r'^គាត់[។!.]*$', 'គាត់មែនទេ?!'),
    (r'^ប៉ា[។!.]*$', 'លោកប៉ា! មានរឿងអីមែនទេ?!'),
    (r'^ម៉ាក់[។!.]*$', 'អ្នកម៉ាក់! កុំភ័យអីណា!'),
    (r'^ស្អី[។!.]*$', 'ស្អីគេហ្នឹង?! មានរឿងអី?!'),
    (r'^អ្វី[។!?]*$', 'ស្អីគេហ្នឹង?! តើមានរឿងអី?!'),
    (r'^ម៉េច[។!.]*$', 'ម៉េចក៏ទៅជាបែបនេះ?!'),
    (r'^ជួយ[។!.]*$', 'ជួយផង! ជួយខ្ញុំផង!'),
    (r'^មិនអីទេ[។.]*$', 'មិនអីនោះទេ មិនបាច់បារម្ភទេ!'),
    (r'^សុំទោស[។.]*$', 'ខ្ញុំពិតជាសុំទោសខ្លាំងណាស់!'),
    (r'^ដឹងហើយ[។.]*$', 'ខ្ញុំដឹងច្បាស់ហើយ មិនបាច់រំលឹកទេ!'),
    (r'^ចេញទៅ[។!.]*$', 'ឆាប់ចេញពីទីនេះភ្លាមទៅ!'),
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
    (r'តើអ្នកកំពុងស្វែងរកការស្លាប់\??', 'ឯងចង់ងាប់មែនទេ?!'),
    (r'ស្វែងរកការស្លាប់', 'ចង់ងាប់'),
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

    # 6. Specific Drama Tropes, Workplace & Family Context Corrections
    (r'ព្រៃអ្វី|ព្រៃ\??', 'អ្នកណាជាលីនឱ្យប្រាកដហ្នឹង?!'),
    (r'គិតថ្លៃខ្លួនឯងយឺត|ថ្លៃខ្លួនឯង.*', 'ហ៊ានបន្លំជាអ្នកមាននៅទីនេះផង?!'),
    (r'បំផ្លាញ​កូន​ថៅកែ|ខូចកូន.*', 'កំពុងពពោះកូនបង្កើតរបស់លោកប្រធាន!'),
    (r'អ្នករស់នៅទូទៅ.*', 'ជំនួយការផ្ទាល់របស់លោកប្រធានក្រុមហ៊ុន!'),
    (r'បើកស្រុកខ្ញុំទាំងមូល.*', 'គ្មានសិទ្ធិមកដេញខ្ញុំចេញពីក្រុមហ៊ុនទេ!'),
    (r'ភាសាអង់គ្លេសនៅក្នុងគ្រួសារ.*', 'រឿងផ្ទៃក្នុងគ្រួសាររបស់ពួកយើង!'),
    (r'មិនបានលួចរឿងនេះទេ.*', 'រឿងនេះមិនមែនជាកំហុសរបស់ខ្ញុំទេ!'),
    (r'មានការយល់ច្រលំច្រើន.*', 'រឿងនេះមានការយល់ច្រឡំច្រើនណាស់!'),
    (r'គោរពអំណោយ.*', 'មនុស្សមិនដឹងគុណគេទាល់តែសោះ!'),
    (r'ចៅហ្វាយចាត់វិធានការថ្នមៗ.*', 'លោកប្រធានមិនបណ្តោយឱ្យឯងរួចខ្លួនជាដាច់ខាត!'),
    (r'ទោះស្តាយក្រោយ.*', 'ដល់ពេលនោះ ទោះស្តាយក្រោយក៏ហួសពេលដែរ!'),
    (r'ទៅមើលមួយភ្លែត.*', 'ឆាប់ទៅមើលនាងភ្លាមទៅ!'),
    (r'ខ្ញុំមិនអាចបោះបង់.*', 'ខ្ញុំពិតជាមិនអស់ចិត្ត និងបារម្ភពីនាងខ្លាំងណាស់!'),
    (r'ម៉ាក់មិនឱ្យ.*រងទុក្ខ.*', 'ម៉ាក់មិនឱ្យនាងរងទុក្ខវេទនា ឬត្រូវគេធ្វើបាបជាដាច់ខាត!'),
    (r'មានទូរស័ព្ទចូល.*', 'មានទូរស័ព្ទមួយទៀតទាក់ទងមកហើយ!'),
    (r'អ្នកព្យួរក.*|ព្យួរវាចុះ.*|បិទទូរស័ព្ទ.*', 'លោកម៉ាក់ចុចបិទទូរស័ព្ទសិនទៅណា!'),
    (r'ឯងកំពុងពពោះកូន.*|មានផ្ទៃពោះ.*', 'កូនកំពុងតែមានផ្ទៃពោះណា៎!'),
    (r'ទំនេរមកផ្ទះ.*', 'ពេលទំនេរ ឆាប់មកលេងផ្ទះណា៎កូន!'),
    (r'ញ៉ាំបាយ.*', 'មកញ៉ាំបាយជុំគ្រួសារនៅផ្ទះយើង!'),
    (r'ខ្ញុំរង់ចាំស៊ុប.*|ចាំស៊ុប.*', 'ម៉ាក់កំពុងរម្ងាស់ស៊ុបក្តៅៗរង់ចាំកូន!'),
    (r'កុំបារម្ភមីង.*|កុំបារម្ភអ៊ំស្រី.*', 'អ្នកមីងកុំបារម្ភអី ខ្ញុំមិនអីទេ!'),
    (r'ខ្ញុំត្រូវបានគេធ្វើបាប.*|ធ្វើបាបនៅក្នុងក្រុមហ៊ុន.*', 'អ្នកមីង... ខ្ញុំត្រូវគេជិះជាន់និងធ្វើបាបនៅក្នុងក្រុមហ៊ុន!'),
    (r'មិនអាចបណ្តេញចេញបានទេ.*|បណ្តេញចេញបានទេ.*', 'មនុស្សចរិតពាលបែបនេះ តើមិនអាចដេញចេញពីក្រុមហ៊ុនបានទេមែនទេ?!'),
    (r'កុំរើឱ្យសោះ.*|ឈប់រើ.*|ឈប់ភ្លាម.*', 'ឈប់ដៃភ្លាម! កុំរើកន្ត្រាក់ឱ្យសោះណា!'),
    (r'មែនហើយ[។.]*$', 'ពិតជាត្រឹមត្រូវហើយ!'),
    (r'យល់ព្រម[។.]*$', 'បានហើយ យល់ព្រមតាមហ្នឹងចុះ!'),
    (r'ចាស[។.]*$', 'ចាស! ខ្ញុំយល់ច្បាស់ហើយ!'),
    (r'បាទ[។.]*$', 'បាទ! ខ្ញុំយល់ច្បាស់ហើយ!'),
]


def enrich_khmer_drama_dialogue(km_text: str, zh_text: str = "", voice: str = "piseth") -> str:
    """
    Guarantees that no Khmer dialogue line is left dry, clipped, or short.
    Expands short utterances into natural, expressive Cambodian TV drama dubbing lines.
    """
    res = km_text.strip()
    if not res:
        return ""

    # Strip trailing artifact words like 'ចាន'
    res = re.sub(r'\s*ចាន[។.!?]*$', '!', res)

    # Clean double punctuation only if ? or ! is actually present
    if '?' in res or '!' in res:
        res = re.sub(r'[?!]+[។.\s]*$', '?!', res)
    res = re.sub(r'([។.!?])\1+', r'\1', res)

    # 1. Direct Regex Expansion for common short words and expressions
    for pattern, replacement in KHMER_DUBBING_POST_CLEANUP:
        if re.search(pattern, res):
            res = re.sub(pattern, replacement, res)
            break

    # 2. Semantic matching for boss/knowledge/agreement
    if re.search(r'ខ្ញុំ.*(?:ចៅហ្វាយ|ថៅកែ)', res):
        return 'ខ្ញុំនេះទើបជាថៅកែពិតប្រាកដ!'
    if re.search(r'ខ្ញុំ.*ដឹង', res):
        return 'ខ្ញុំដឹងតាំងពីដំបូងមកម្ល៉េះ!'

    # 3. Contextual expansions for short single-word responses
    is_male = (voice == "piseth")
    if len(res) <= 15:
        if res in ("ល្អ", "ល្អ!", "ល្អណាស់", "យល់ព្រម", "បាន", "បាន!", "បានហើយ"):
            return "បានហើយ យល់ព្រមតាមហ្នឹងចុះ!"
        elif res in ("បាទ", "បាទ!", "ចាស", "ចាស!"):
            return "បាទ! ខ្ញុំយល់ច្បាស់ហើយ!" if is_male else "ចាស! ខ្ញុំយល់ច្បាស់ហើយ!"
        elif res in ("មែន", "មែន!", "ត្រូវ", "ត្រូវហើយ"):
            return "ពិតជាត្រឹមត្រូវហើយ!"
        elif res in ("អ្នក", "ឯង", "លោក", "នាង"):
            return "ឯងកុំថ្លើមធំពេកឱ្យសោះ!" if is_male else "ឯង...ឯងកុំមកមើលងាយខ្ញុំឱ្យសោះណា!"
        elif res in ("ទៅ", "ដើរ", "ចេញ"):
            return "ឆាប់ចេញពីទីនេះភ្លាមទៅ!"
        elif res in ("កូន", "កូនប្រុស", "កូនស្រី"):
            return "កូនសម្លាញ់! យ៉ាងម៉េចហើយ?!"
        elif res in ("ម៉ាក់", "អ្នកម៉ាក់", "ម៉ាក់!"):
            return "អ្នកម៉ាក់! កុំភ័យអីណា!"
        elif res in ("ប៉ា", "លោកប៉ា", "ប៉ា!"):
            return "លោកប៉ា! កុំបារម្ភអី!"
        elif res in ("បង", "អូន"):
            return "អូនកុំភ័យអីណា!" if is_male else "បង...ជួយខ្ញុំផង!"
        elif res in ("ឈប់", "ឈប់!"):
            return "ឈប់ដៃភ្លាម! កុំរើឱ្យសោះ!"
        elif res.endswith("?!") or res.endswith("?"):
            if "ស្អី" in res or "អ្វី" in res:
                res = "ស្អីគេហ្នឹង?! តើមានរឿងអី?!"
            elif "ម៉េច" in res:
                res = "ម៉េចក៏ទៅជាបែបនេះ?!"
            elif "ឯណា" in res:
                res = "តើនៅឯណាឱ្យប្រាកដហ្នឹង?!"
            elif "នរណា" in res or "អ្នកណា" in res:
                res = "តើនរណាគេហ្នឹង?!"
            elif "ល្ងង់" in res:
                res = "ឯងឆ្កួតឬក៏ល្ងង់ឱ្យប្រាកដហ្នឹង?!"
            elif "មែនទេ" in res:
                res = "ជារឿងពិតមែនទេ?!"
            elif not res.endswith("ហ្នឹង?!") and not res.endswith("ទេ?!"):
                res = f"{res.rstrip('?!')}ឱ្យប្រាកដហ្នឹង?!"
        elif "មិនអី" in res:
            res = "មិនអីនោះទេ មិនបាច់បារម្ភទេ!"
        elif "ជួយ" in res:
            res = "ជួយផង! ជួយខ្ញុំផង!"
        elif "សុំទោស" in res:
            res = "ខ្ញុំពិតជាសុំទោសខ្លាំងណាស់!"
        elif "អរគុណ" in res:
            res = "អរគុណច្រើនណាស់ណា!"

    return res.strip()


class DramaTranslator:
    def __init__(self, gemini_api_key: Optional[str] = None):
        self.api_keys: List[str] = []
        self.clients: List[Any] = []
        self.current_key_idx = 0
        raw_key = gemini_api_key or os.environ.get("GEMINI_API_KEY", "")
        if not raw_key:
            for p in [Path("data/ai_provider_config.json"), Path("data/ai_config.json")]:
                if p.exists():
                    try:
                        with open(p, "r", encoding="utf-8") as f:
                            cfg = json.load(f)
                            raw_key = cfg.get("keys_raw", "") or "\n".join(cfg.get("keys", []))
                            if raw_key:
                                break
                    except Exception:
                        pass
        if raw_key:
            keys = [k.strip() for k in raw_key.replace(",", "\n").splitlines() if k.strip()]
            self.set_api_keys(keys)
        else:
            self.api_key = ""
            self.client = None

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
        res = km_text.strip()
        for pattern, replacement in KHMER_DUBBING_POST_CLEANUP:
            res = re.sub(pattern, replacement, res)
        return enrich_khmer_drama_dialogue(res, zh_text, voice)

    async def translate_text_free(self, text: str, source_lang: str = "auto", voice: str = "piseth") -> str:
        """
        Robust free translation with pre-normalization and post-polishing for film dubbing.
        """
        if not text or not text.strip():
            return ""

        cleaned = self._pre_normalize_chinese(text.strip())

        sl = "auto" if source_lang in ("auto", "", None) else source_lang
        if sl in ("zh", "chinese"):
            sl = "zh-CN"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Referer": "https://translate.google.com/"
        }

        # 1. Primary: Google Clients5 API
        try:
            url1 = "https://clients5.google.com/translate_a/t"
            params1 = {
                "client": "dict-chrome-ex",
                "sl": sl,
                "tl": "km",
                "q": cleaned
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
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
            async with httpx.AsyncClient(timeout=10.0) as client:
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
        Assign STRICTLY either 'piseth' (Male) or 'sreymom' (Female).
        NO 3-4 voices, NO pitch shifting (pitch_hz=0), NO rate shifting (rate_percent=0).
        """
        if target_voice_override in ("piseth", "sreymom"):
            return {
                "voice": target_voice_override,
                "rate_percent": 0,
                "pitch_hz": 0,
                "character_role": "ពិសិដ្ឋ (Piseth)" if target_voice_override == "piseth" else "ស្រីមុំ (Sreymom)"
            }

        # Check existing voice attribute if already detected by STT acoustic pitch
        item_voice = str(item.get("voice", "")).lower()
        if item_voice in ("piseth", "sreymom"):
            return {
                "voice": item_voice,
                "rate_percent": 0,
                "pitch_hz": 0,
                "character_role": "ពិសិដ្ឋ (Piseth - តួប្រុស)" if item_voice == "piseth" else "ស្រីមុំ (Sreymom - តួស្រី)"
            }

        speaker_name = str(item.get("speaker", "")).lower()
        detected_role = str(item.get("detected_role", "")).lower()
        speaker_idx = item.get("speaker_idx", 1)

        # Check for Female character indicators:
        is_female = (
            "female" in speaker_name or
            "តួស្រី" in speaker_name or
            "ស្រី" in speaker_name or
            "ម្តាយ" in speaker_name or
            "sreymom" in speaker_name or
            detected_role in ("female", "elder_female")
        )

        # Check for Male character indicators:
        is_male = (
            "male" in speaker_name or
            "តួប្រុស" in speaker_name or
            "ប្រុស" in speaker_name or
            "ឪពុក" in speaker_name or
            "piseth" in speaker_name or
            detected_role in ("male", "elder_male")
        )

        if is_female and not is_male:
            return {
                "voice": "sreymom",
                "rate_percent": 0,
                "pitch_hz": 0,
                "character_role": "ស្រីមុំ (Sreymom - តួស្រី)"
            }
        elif is_male and not is_female:
            return {
                "voice": "piseth",
                "rate_percent": 0,
                "pitch_hz": 0,
                "character_role": "ពិសិដ្ឋ (Piseth - តួប្រុស)"
            }
        else:
            if speaker_idx % 2 == 0:
                return {
                    "voice": "sreymom",
                    "rate_percent": 0,
                    "pitch_hz": 0,
                    "character_role": "ស្រីមុំ (Sreymom - តួស្រី)"
                }
            else:
                return {
                    "voice": "piseth",
                    "rate_percent": 0,
                    "pitch_hz": 0,
                    "character_role": "ពិសិដ្ឋ (Piseth - តួប្រុស)"
                }

    async def translate_dialogues(
        self,
        dialogues: List[Dict[str, Any]],
        mode: str = "drama_dubbing",
        source_lang: str = "auto",
        target_voice_override: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Translate dialogue items into authentic Khmer drama dubbing lines.
        Strictly applies only TWO voices: Piseth and Sreymom (rate=0, pitch=0).
        Enriches short lines into full, expressive TV drama sentences.
        """
        if not dialogues:
            return []

        # 1. Gemini AI Studio Translation with robust per-chunk error recovery
        translated_items: Dict[int, Dict[str, Any]] = {}

        if self.clients and self.api_keys:
            try:
                chunk_size = 18
                for i in range(0, len(dialogues), chunk_size):
                    chunk = dialogues[i:i + chunk_size]
                    # Add duration_sec so AI produces length-matched speech that finishes on-time
                    enriched_chunk = []
                    for c in chunk:
                        c_copy = dict(c)
                        c_dur = round(float(c.get("end", 0.0)) - float(c.get("start", 0.0)), 2)
                        c_copy["duration_sec"] = max(0.5, c_dur)
                        enriched_chunk.append(c_copy)

                    prompt = f"""Mode: {mode} (Authentic Cambodian TV Drama Dubbing)
Source Language: {source_lang}
Input script items in JSON (with target speaking duration 'duration_sec'):
{json.dumps(enriched_chunk, ensure_ascii=False, indent=2)}

CRITICAL DUBBING TIMING & LIP-SYNC RULES:
1. Translate each dialogue item into emotional, dramatic, natural spoken Khmer dubbing script ('text_km') like Piseth and Sreymom.
2. LIP-SYNC DURATION MATCHING: Adapt the length of 'text_km' to 'duration_sec':
   - Short lines (duration < 1.4s): Keep translation punchy and concise (3-6 words), NEVER write long verbose sentences.
   - Longer scenes: Expand into dramatic, authentic Cambodian TV dialogue.
3. Assign 'voice' strictly to either 'piseth' (Male Lead & supporting) or 'sreymom' (Female Lead & supporting).
4. Return ONLY valid JSON array with keys: id, start, end, text_original, text_km, speaker, voice, rate_percent, pitch_hz."""

                    active_client = self.get_client() or self.client
                    response = None
                    for m_name in ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']:
                        try:
                            response = active_client.models.generate_content(
                                model=m_name,
                                contents=prompt,
                                config=types.GenerateContentConfig(
                                    system_instruction=DRAMA_PROMPT_SYSTEM,
                                    response_mime_type="application/json"
                                )
                            )
                            if response and response.text:
                                break
                        except Exception as call_err:
                            err_msg = str(call_err)
                            if "404" in err_msg or "NOT_FOUND" in err_msg:
                                continue
                            alt_client = self.get_client()
                            if alt_client and alt_client != active_client:
                                try:
                                    response = alt_client.models.generate_content(
                                        model=m_name,
                                        contents=prompt,
                                        config=types.GenerateContentConfig(
                                            system_instruction=DRAMA_PROMPT_SYSTEM,
                                            response_mime_type="application/json"
                                        )
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

        # 2. Fill any missing items via High-Performance Drama Dubbing Engine (Zero Missing Lines Guarantee)
        missing_indices = [idx for idx in range(len(dialogues)) if idx not in translated_items]
        if missing_indices:
            sem = asyncio.Semaphore(8)

            async def _translate_single(global_idx: int):
                async with sem:
                    item = dialogues[global_idx]
                    orig_text = item.get("text") or item.get("text_original", "")
                    start = item.get("start", 0.0)
                    end = item.get("end", 0.0)

                    # Determine strictly Piseth or Sreymom (pitch=0, rate=0)
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

                    final_text_km = enrich_khmer_drama_dialogue(text_km, orig_text, chosen_voice)

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
                    "text_km": enrich_khmer_drama_dialogue(orig_text, orig_text, v_info["voice"]),
                    "voice": v_info["voice"],
                    "rate_percent": 0,
                    "pitch_hz": 0
                })

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
