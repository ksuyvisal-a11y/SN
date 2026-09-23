import sys
sys.stdout.reconfigure(encoding='utf-8')
import sqlite3
import json

conn = sqlite3.connect("data/hongguo_catalog.db")
cur = conn.cursor()
cur.execute("SELECT id, title, title_cn, category, total_episodes, poster FROM hongguo_dramas LIMIT 10")
rows = cur.fetchall()
for r in rows:
    print(r)
