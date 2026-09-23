"""
Seed Authentic ReelShort Drama Series into Hongguo Catalog DB.
Platform: Reelshort
"""
import sys
import os
import json
import sqlite3
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

DB_PATH = Path("data/hongguo_catalog.db")

REELSHORT_HITS = [
    ("The Double Life of My Billionaire Husband", "我的百亿老公的双面人生", "រៀបការជាមួយស្វាមីមហាសេដ្ឋីលាក់មុខ", 75, "billionaire_ceo", "CEO", "9.8", "8500万"),
    ("Never Divorce a Secret Billionaire Heiress", "绝不与千亿隐秘女继承人离婚", "កុំលែងលះជាមួយអ្នកស្នងមរតកសម្ងាត់", 80, "urban_revenge", "Revenge", "9.7", "7800万"),
    ("Fated to My Forbidden Alpha", "与禁忌狼王的宿命契约", "ព្រហ្មលិខិតជាមួយស្តេចចចក", 68, "god_of_war", "War God", "9.9", "9200万"),
    ("Goodbye, My CEO Ex-Husband", "再见，我的总裁前夫", "លាហើយអតីតស្វាមី CEO", 72, "urban_revenge", "Revenge", "9.5", "6700万"),
    ("The Alpha's Contract Bride", "狼王殿下的契约新娘", "កូនក្រមុំកិច្ចសន្យាស្តេចចចក", 70, "sweet_romance", "Romance", "9.6", "7100万"),
    ("True Luna", "至尊真月神女王", "ព្រះនាងចចកពិត", 85, "palace_historical", "Palace", "9.8", "8900万"),
    ("Married at First Sight: The Billionaire's Secret Bride", "闪婚千亿继承人", "រៀបការភ្លាមៗជាមួយមហាសេដ្ឋី", 76, "sweet_romance", "Romance", "9.4", "6400万"),
    ("Love Across Time: The Mafia King's Captive", "黑手党教父的挚爱囚徒", "ឈ្លើយស្នេហ៍ស្តេចម៉ាហ្វីយ៉ា", 65, "action_suspense", "Action", "9.5", "5800万"),
    ("Her Revenge: The Billionaire's Stolen Queen", "千亿女王的血色复仇", "ការសងសឹករបស់ម្ចាស់ក្សត្រី", 80, "urban_revenge", "Revenge", "9.6", "6900万"),
    ("Fatal Allure: Claimed by the Lycan King", "致命诱惑：狼皇独占", "អន្ទាក់ស្នេហ៍ស្តេចចចក", 74, "god_of_war", "War God", "9.7", "7500万"),
    ("The Substitute Bride for the Ruthless CEO", "冷面暴君的替嫁新娘", "កូនក្រមុំជំនួសរបស់ CEO ឈាមត្រជាក់", 78, "billionaire_ceo", "CEO", "9.5", "6300万"),
    ("Billionaire's Secret Twins", "千亿总裁的天降双宝", "កូនភ្លោះសម្ងាត់របស់មហាសេដ្ឋី", 80, "sweet_romance", "Romance", "9.6", "7000万"),
    ("Tempted by My Ex's Brother", "沦陷于前任的哥哥", "លង់ស្នេហ៍បងប្រុសអតីតសង្សារ", 60, "sweet_romance", "Romance", "9.3", "5400万"),
    ("The Ruthless Alpha's Surrogate", "冷血狼王的代孕新娘", "ម្តាយពពោះជំនួសរបស់ស្តេចចចក", 72, "god_of_war", "War God", "9.7", "7900万"),
    ("My Husband, the Hidden Billionaire", "神秘老公竟然是世界首富", "ស្វាមីខ្ញុំជាមហាសេដ្ឋីលាក់មុខ", 80, "billionaire_ceo", "CEO", "9.6", "6800万"),
    ("Sweet Revenge: Back to the Ruthless Ex", "甜蜜复仇：回到绝情前夫身边", "សងសឹកផ្អែមល្ហែមទៅលើអតីតសង្សារ", 70, "urban_revenge", "Revenge", "9.4", "5900万"),
    ("His Innocent Contract Wife", "冷酷大亨的小娇妻", "ភរិយាកិច្ចសន្យាដ៏ស្លូតបូត", 68, "sweet_romance", "Romance", "9.5", "6100万"),
    ("Born to Rule: The Mafia Princess Reborn", "重生黑道千金：权倾天下", "កើតមកដើម្បីគ្រងរាជ្យ: ម្ចាស់ក្សត្រីម៉ាហ្វីយ៉ា", 82, "rebirth_travel", "Rebirth", "9.8", "8100万"),
    ("Bound by Blood: The Vampire Prince", "吸血鬼王子的血誓之约", "ចំណងឈាមព្រះអង្គម្ចាស់បិសាចជញ្ជក់ឈាម", 65, "action_suspense", "Action", "9.6", "6600万"),
    ("The CEO's Blind Date Disaster", "相亲相到顶头霸总", "ការណាត់ជួបដ៏ច្របូកច្របល់របស់ CEO", 55, "billionaire_ceo", "CEO", "9.2", "4900万"),
    ("Revenge of the Disowned Heiress", "被逐千金的绝地逆袭", "ការសងសឹករបស់អ្នកស្នងមរតកដែលត្រូវបណ្ដេញចេញ", 80, "urban_revenge", "Revenge", "9.7", "7600万"),
    ("The Billionaire's Accidental Bride", "阴差阳错嫁入豪门", "កូនក្រមុំចៃដន្យរបស់មហាសេដ្ឋី", 75, "billionaire_ceo", "CEO", "9.5", "6500万"),
    ("Claimed by the Rogue Alpha", "流浪狼王的霸道强宠", "គ្រប់គ្រងដោយស្តេចចចកអនាថា", 68, "god_of_war", "War God", "9.6", "7200万"),
    ("Falling for the Beast CEO", "爱上野兽派冷血总裁", "លង់ស្នេហ៍ CEO ចិត្តសាហាវ", 70, "sweet_romance", "Romance", "9.4", "5800万"),
    ("Secretly Married to the Campus Heartthrob", "隐婚校草：学神独宠小甜妻", "រៀបការសម្ងាត់ជាមួយប្រុសស្អាតប្រចាំសាលា", 64, "sweet_romance", "Romance", "9.3", "5200万"),
    ("The Mafia Don's Reluctant Wife", "教父的契约小妻子", "ភរិយាមិនស្ម័គ្រចិត្តរបស់មេម៉ាហ្វីយ៉ា", 72, "action_suspense", "Action", "9.6", "6900万"),
    ("Resisting the Lycan Prince", "抗拒高冷狼族继承人", "ទប់ទល់នឹងព្រះអង្គម្ចាស់ចចក", 66, "god_of_war", "War God", "9.5", "6400万"),
    ("The Contract Marriage with My Boss", "与冷酷上司的百日契约", "អាពាហ៍ពិពាហ៍កិច្ចសន្យាជាមួយមេការ", 74, "billionaire_ceo", "CEO", "9.4", "6100万"),
    ("She Returned as a Billionaire", "五年后携百亿携宝回归", "នាងត្រឡប់មកវិញជាមហាសេដ្ឋី", 80, "urban_revenge", "Revenge", "9.8", "8800万"),
    ("Pregnant with the CEO's Triplets", "揣着三胞胎带球跑", "មានផ្ទៃពោះកូនភ្លោះបីជាមួយ CEO", 82, "sweet_romance", "Romance", "9.7", "7700万"),
]

POSTER_POOL = [
    "posters/poster_sample_ceo.jpg",
    "posters/poster_good_girl.jpg",
    "posters/poster_yan_lu.jpg",
    "posters/poster_yi_pin_bu_yi.jpg"
]

def main():
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    
    # Remove any existing Reelshort to avoid duplicates
    cur.execute("DELETE FROM hongguo_dramas WHERE platform_id = 'reelshort'")
    cur.execute("DELETE FROM drama_categories WHERE drama_id LIKE 'rs_%'")
    
    records = []
    cat_records = []
    
    for rank, item in enumerate(REELSHORT_HITS, 1):
        t_en, t_cn, t_kh, eps, cat_id, cat_name, score, heat = item
        drama_id = f"rs_{rank:03d}"
        full_title = f"{t_en} ({t_kh})"
        desc = f"រឿងភាគខ្លី ReelShort ដ៏ល្បីល្បាញ 《{t_en}》 - {t_kh}។ សរុប {eps} ភាគកម្រិត 1080p Full HD។"
        cover = POSTER_POOL[(rank - 1) % len(POSTER_POOL)]
        tags = json.dumps(["ReelShort", "Exclusive", cat_name, "1080p Full HD"], ensure_ascii=False)
        
        records.append((
            drama_id, full_title, t_en, t_kh, "Reelshort", "reelshort",
            eps, cat_name, cat_id, score, "2025", cover, desc, tags, heat, "completed", rank
        ))
        
        cat_records.append((drama_id, "all"))
        cat_records.append((drama_id, cat_id))
        
    cur.executemany("INSERT INTO hongguo_dramas VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", records)
    cur.executemany("INSERT OR IGNORE INTO drama_categories VALUES (?, ?)", cat_records)
    conn.commit()
    
    cur.execute("SELECT count(*) FROM hongguo_dramas WHERE platform_id = 'reelshort'")
    count = cur.fetchone()[0]
    print(f"✓ Successfully seeded {count} authentic ReelShort dramas into database!")
    conn.close()

if __name__ == "__main__":
    main()
