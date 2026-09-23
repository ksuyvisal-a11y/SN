import sys
from pathlib import Path
import json

sys.stdout.reconfigure(encoding='utf-8')

# Ensure parent directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from server import app
import data.hongguo_db as db

def test_api():
    client = app.test_client()

    print("--- 1. Testing Categories Endpoint ---")
    res = client.get('/api/downloader/categories')
    assert res.status_code == 200, f"Status code: {res.status_code}"
    cat_data = res.get_json()
    assert cat_data["success"] is True
    print(f"Total categories: {len(cat_data['categories'])}")
    for c in cat_data["categories"]:
        print(f"  [{c['id']}] {c.get('badge')} -> {c.get('name')}")

    print("\n--- 2. Testing Image 2 First 6 Dramas ---")
    res = client.get('/api/downloader/catalog?platform=hongguo&category=all&page=1&limit=6')
    assert res.status_code == 200
    cat_res = res.get_json()
    assert cat_res["success"] is True
    dramas = cat_res["dramas"]
    assert len(dramas) == 6

    expected_titles = [
        "宴律，你的白月光回国了",
        "十八岁太奶奶驾到，重整家族",
        "好一个乖乖女",
        "一品布衣",
        "侯府主母要寿终正寝",
        "暗潮涌动"
    ]

    for idx, (d, exp_title) in enumerate(zip(dramas, expected_titles)):
        clean_title = d["title_cn"].replace("《", "").replace("》", "").strip()
        print(f"Card {idx+1}: '{clean_title}' | Poster: {d['poster']} | Cat: {d['category_id']}")
        assert clean_title == exp_title, f"Expected {exp_title}, got {clean_title}"
        assert d["poster"].startswith("posters/"), f"Poster should be in posters/, got {d['poster']}"

    print("\n--- 3. Testing Category Filtering ---")
    categories_to_test = [
        ("urban_revenge", "狂龙出狱之逆袭绝顶"),
        ("billionaire_ceo", "好一个乖乖女"),
        ("god_of_war", "一品布衣"),
        ("rebirth_travel", "十八岁太奶奶驾到，重整家族"),
        ("sweet_romance", "宴律，你的白月光回国了"),
        ("divine_doctor", "神医下山之绝世医仙"),
        ("palace_historical", "侯府主母要寿终正寝"),
        ("action_suspense", "暗潮涌动"),
    ]

    for cat_id, expected_top in categories_to_test:
        res = client.get(f'/api/downloader/catalog?platform=hongguo&category={cat_id}&page=1&limit=2')
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        top_drama = data["dramas"][0]
        top_title = top_drama["title_cn"].replace("《", "").replace("》", "").strip()
        print(f"Filter [{cat_id}]: Total {data['total_count']} -> Top: '{top_title}'")
        assert top_title == expected_top, f"Expected {expected_top}, got {top_title}"

    print("\n--- 4. Testing Drama Detail & Preview ---")
    res = client.get('/api/downloader/drama/hg_00001')
    assert res.status_code == 200
    d_data = res.get_json()
    assert d_data["success"] is True
    assert len(d_data["episodes"]) == 80
    print(f"Drama hg_00001 details: '{d_data['drama']['title']}', Episodes: {len(d_data['episodes'])}")

    print("\nALL BACKEND & API TESTS PASSED PERFECTLY!")

if __name__ == '__main__':
    test_api()
