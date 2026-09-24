import re

def get_search_queries_for_title_v2(raw_title: str):
    if not raw_title:
        return []
    candidates = []
    
    def add_cand(c: str):
        c = c.strip()
        # Clean punctuation from ends
        c = re.sub(r'^[^\w\u4e00-\u9fff]+|[^\w\u4e00-\u9fff]+$', '', c)
        if c and len(c) >= 2 and c not in candidates:
            candidates.append(c)

    # 1. Extract content within brackets 《...》, 【...】, (...), etc.
    bracketed = re.findall(r'[《【（「『\[](.*?)[》】）」』\]]', raw_title)
    base_titles = bracketed if bracketed else [raw_title]

    for base in base_titles:
        # Strip Khmer subtitle / English parts / trailing notes
        clean = base.split(' - ')[0].split(' (')[0].strip()
        # Remove season designations
        clean_no_season = re.sub(r'第[一二三四五六七八九十0-9]+[季部]', '', clean).strip()
        clean_no_season = re.sub(r'[\(（]?[全大]结局[\)）]?', '', clean_no_season).strip()
        clean_no_season = re.sub(r'[\(（]?全集[\)）]?', '', clean_no_season).strip()
        add_cand(clean_no_season)

        # 2. Split on punctuation marks: ： : ， , ！ ! ？ ? 、 · \s
        parts = [p.strip() for p in re.split(r'[：:，,！？!？、·\s\-_—]+', clean_no_season) if p.strip()]
        for p in parts:
            if len(p) >= 2:
                add_cand(p)

        # 3. Chinese-only substring
        ch_chars = "".join(re.findall(r'[\u4e00-\u9fff]', clean_no_season))
        if len(ch_chars) >= 4:
            add_cand(ch_chars[:4])
            if len(ch_chars) >= 6:
                add_cand(ch_chars[:5])
        elif len(ch_chars) >= 2:
            add_cand(ch_chars)

    return candidates

test_samples = [
    '《心声藏不住：裴总别装了》 - រឿងភាគ 心声藏不住：裴总别装了',
    '《渔民直播：我的渔网通宝库!》 - រឿងភាគ 渔民直播：我的渔网通宝库!',
    '《致命团建日》 - រឿងភាគ 致命团建日',
    '《糯糯下山，师兄们都慌了第三季》',
    'The Double Life of My Billionaire Husband (រៀបការជាមួយស្វាមីមហាសេដ្ឋីលាក់មុខ)'
]

for s in test_samples:
    print(s)
    print(" ->", get_search_queries_for_title_v2(s))
    print()
