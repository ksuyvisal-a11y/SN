import sys
sys.stdout.reconfigure(encoding='utf-8')
import re
from typing import List

def get_search_queries_for_title(raw_title: str) -> List[str]:
    """Generate intelligent list of query candidates from title."""
    if not raw_title:
        return []
        
    candidates = []
    
    # 1. Extract content within 《...》
    m_book = re.findall(r'《(.*?)》', raw_title)
    base_titles = m_book if m_book else [raw_title]
    
    for base in base_titles:
        # Strip Khmer subtitle / English parts
        clean = base.split(' - ')[0].split(' (')[0].strip()
        # Remove season numbers like 第一季, 第二季, 第三季
        clean_no_season = re.sub(r'第[一二三四五六七八九十0-9]+[季部]', '', clean).strip()
        
        # Candidate 1: full clean title
        if clean_no_season and clean_no_season not in candidates:
            candidates.append(clean_no_season)
            
        # Candidate 2: title before punctuation (：, :, ，, ,, !, !)
        parts = re.split(r'[：:，,！？!\s]', clean_no_season)
        if parts and parts[0] and len(parts[0]) >= 2:
            prefix = parts[0].strip()
            if prefix not in candidates:
                candidates.append(prefix)
                
        # Candidate 3: first 4-6 Chinese chars if long
        chinese_chars = "".join(re.findall(r'[\u4e00-\u9fff]', clean_no_season))
        if len(chinese_chars) >= 4:
            c4 = chinese_chars[:4]
            if c4 not in candidates:
                candidates.append(c4)
                
    return candidates

if __name__ == "__main__":
    titles = [
        "《东北话事人》 - រឿងភាគពិសេស 东北话事人",
        "《糯糯下山，师兄们都慌了第三季》",
        "《无双神侯》",
        "《战神归乡：谁敢动我姐姐》",
        "《离婚后我独美，你哭什么》",
        "《被赶出豪门，假千金成团宠逆天改命》"
    ]
    for t in titles:
        print(f"'{t}' => {get_search_queries_for_title(t)}")
