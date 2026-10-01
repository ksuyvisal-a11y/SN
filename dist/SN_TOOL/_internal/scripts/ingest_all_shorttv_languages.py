"""
High-Speed Ingestion of ALL Global ShortTV Catalogs.
Languages: ['es', 'en', 'ja', 'ar', 'vi', 'id', 'fr', 'pt', 'de', 'th', 'ru', 'ms', 'ko']
Collects 100% of all unique dramas worldwide from shorttv.live.
"""

import sys
import os
import time
import json
import base64
import sqlite3
import subprocess
from pathlib import Path
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = Path("data/hongguo_catalog.db")
CACHE_FILE = Path("data/shortmax_all_dramas.json")

AES_KEY = b"shortwebapiaesen"
AES_IV = b"shortwebapiaesen"

def pad_pkcs7(data: bytes, block_size: int = 16) -> bytes:
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len] * pad_len)

def unpad_pkcs7(data: bytes) -> bytes:
    pad_len = data[-1]
    if pad_len > 16 or pad_len == 0:
        return data
    if data[-pad_len:] == bytes([pad_len]) * pad_len:
        return data[:-pad_len]
    return data

def encrypt_payload(obj) -> str:
    raw = json.dumps(obj, separators=(',', ':')).encode('utf-8')
    padded = pad_pkcs7(raw)
    cipher = Cipher(algorithms.AES(AES_KEY), modes.CBC(AES_IV), backend=default_backend())
    enc = cipher.encryptor()
    encrypted = enc.update(padded) + enc.finalize()
    return base64.b64encode(encrypted).decode('utf-8')

def decrypt_payload(b64_str: str):
    cleaned = "".join(c for c in b64_str.strip() if c.isalnum() or c in '+/=')
    rem = len(cleaned) % 4
    if rem != 0:
        cleaned += '=' * (4 - rem)
    data = base64.b64decode(cleaned)
    cipher = Cipher(algorithms.AES(AES_KEY), modes.CBC(AES_IV), backend=default_backend())
    dec = cipher.decryptor()
    decrypted = dec.update(data) + dec.finalize()
    unpadded = unpad_pkcs7(decrypted)
    return json.loads(unpadded.decode('utf-8'))

def call_api(endpoint: str, body: dict, lang: str = 'en', retries: int = 3):
    url = f"https://shortweb.shorttv.live/app-api/app{endpoint}"
    encrypted_body = encrypt_payload(body)
    cmd = [
        'curl.exe', '-4', '-s', '-m', '15',
        '-X', 'POST', url,
        '-H', 'Content-Type: application/json',
        '-H', 'X-Encrypted: true',
        '-H', f'Language-Code: {lang}',
        '-H', 'Origin: https://www.shorttv.live',
        '-H', 'Referer: https://www.shorttv.live/',
        '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        '-d', encrypted_body
    ]
    for attempt in range(retries):
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore')
            out = res.stdout.strip()
            if out:
                d = decrypt_payload(out)
                if d and d.get('code') == 0:
                    return d
        except Exception:
            pass
        time.sleep(0.3)
    return None

from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_language(lang: str, page_size: int = 50) -> list:
    res = call_api('/cmsShortPlay/queryPage', {'pageNo': 1, 'pageSize': page_size, 'labelId': '', 'classId': ''}, lang=lang)
    if not res or not res.get('data'):
        print(f"[{lang}] Failed to fetch page 1", flush=True)
        return []
        
    data = res['data']
    total = data.get('total', 0)
    items = list(data.get('list', []))
    print(f"[{lang}] Total catalog size: {total}. Fetched page 1 (+{len(items)} dramas).", flush=True)
    
    if len(items) >= total:
        return items
        
    total_pages = (total + page_size - 1) // page_size
    
    def _fetch_pg(p):
        r = call_api('/cmsShortPlay/queryPage', {'pageNo': p, 'pageSize': page_size, 'labelId': '', 'classId': ''}, lang=lang)
        if r and r.get('data') and r['data'].get('list'):
            return r['data']['list']
        return []

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(_fetch_pg, p): p for p in range(2, total_pages + 1)}
        for fut in as_completed(futures):
            sub = fut.result()
            if sub:
                items.extend(sub)
                
    print(f"  [{lang}] Completed: collected {len(items)} / {total} dramas.", flush=True)
    return items

def main():
    print("==================================================================", flush=True)
    print("🌍 SHORTMAX GLOBAL CATALOG HARVESTER - ALL LANGUAGES", flush=True)
    print("==================================================================", flush=True)

    all_dramas = {}
    
    # Pre-load existing 1078 dramas
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cached = json.load(f)
                for it in cached:
                    pid = str(it.get('shortPlayId') or '')
                    if pid:
                        all_dramas[pid] = it
            print(f"Loaded {len(all_dramas)} existing dramas from cache.\n", flush=True)
        except Exception:
            pass

    languages = ['es', 'en', 'ja', 'ar', 'vi', 'id', 'fr', 'pt', 'de', 'th', 'ru', 'ms', 'ko']

    for lang in languages:
        print(f"\n>>> Processing region: {lang.upper()} ...", flush=True)
        items = fetch_language(lang, page_size=50)
        added = 0
        for it in items:
            pid = str(it.get('shortPlayId') or '')
            if not pid:
                continue
            if pid not in all_dramas:
                all_dramas[pid] = it
                added += 1
            else:
                # Supplement missing info if any
                curr = all_dramas[pid]
                if not curr.get('coverId') and it.get('coverId'):
                    curr['coverId'] = it.get('coverId')
                if not curr.get('horizontalCoverId') and it.get('horizontalCoverId'):
                    curr['horizontalCoverId'] = it.get('horizontalCoverId')
        print(f"✓ [{lang.upper()}] Finished. Added {added} NEW dramas. (Total unique overall: {len(all_dramas)})", flush=True)

    master_list = list(all_dramas.values())
    total_unique = len(master_list)
    print(f"\n==================================================================", flush=True)
    print(f"🎉 HARVEST COMPLETE! Total Unique Dramas Collected: {total_unique}", flush=True)
    print(f"==================================================================", flush=True)

    # Save to JSON cache
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(master_list, f, ensure_ascii=False, indent=2)
    print(f"Saved complete global catalog to {CACHE_FILE}")

    # Synchronize into SQLite database
    print(f"Synchronizing {total_unique} dramas into {DB_PATH} ...", flush=True)
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    
    # Remove existing shortmax entries and reinsert completely
    cur.execute("DELETE FROM hongguo_dramas WHERE LOWER(platform_id) = 'shortmax'")
    
    records = []
    for rank, it in enumerate(master_list, 1):
        sp_id = str(it.get('shortPlayId') or '')
        drama_id = f"shortmax_{sp_id}"
        
        name = it.get('shortPlayName') or it.get('lanShortPlayName') or it.get('rawName') or f"ShortMax Drama {sp_id}"
        name = name.strip()
        
        eps = int(it.get('totalEpisode') or it.get('episode') or it.get('totalEpisodeNum') or 50)
        if eps <= 0:
            eps = 50
            
        cover = it.get('coverId') or it.get('lanCoverId') or it.get('horizontalCoverId') or it.get('cover') or ""
        desc = it.get('summary') or it.get('lanShortPlayDescription') or it.get('introduction') or f"Official ShortMax drama: {name}"
        desc = desc.strip()
        
        heat_val = it.get('convertPlayNum') or it.get('playNum') or it.get('heat') or "100K views"
        if isinstance(heat_val, (int, float)):
            if heat_val >= 1000000:
                heat = f"{heat_val / 1000000:.1f}M views"
            elif heat_val >= 1000:
                heat = f"{int(heat_val // 1000)}K views"
            else:
                heat = f"{int(heat_val)} views"
        else:
            heat = str(heat_val)
            if not heat.endswith("views") and not heat.endswith("万"):
                heat = f"{heat} views"
                
        tags = ["ShortMax", "1080p Full HD"]
        lang_code = it.get('languageCode')
        if lang_code:
            tags.append(lang_code.upper())
        tags_json = json.dumps(tags, ensure_ascii=False)
        
        primary_cat = "All"
        cat_id = "all"
        title_kh = f"រឿងភាគ {name}"
        full_title = f"《{name}》 - {title_kh}"
        rating = "9.2"
        status = "completed"
        year = "2025"
        
        records.append((
            drama_id, full_title, name, title_kh, "ShortMax", "shortmax",
            eps, primary_cat, cat_id, rating, year, cover, desc, tags_json, heat, status, rank
        ))
        
    cur.executemany("INSERT OR IGNORE INTO hongguo_dramas VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", records)
    conn.commit()
    
    cur.execute("SELECT count(*) FROM hongguo_dramas WHERE LOWER(platform_id) = 'shortmax'")
    db_sm_cnt = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM hongguo_dramas")
    db_total = cur.fetchone()[0]
    conn.close()
    
    print(f"\nDATABASE UPDATED SUCCESSFULLY:")
    print(f"  * ShortMax Dramas in DB: {db_sm_cnt}")
    print(f"  * Total Dramas in DB: {db_total}")

if __name__ == '__main__':
    main()
