import sqlite3
import json
from pathlib import Path

DB_PATH = Path("data/hongguo_catalog.db")
CACHE_JSON_PATH = Path("data/reelshort_catalog.json")

conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()

cur.execute("SELECT count(*) FROM hongguo_dramas WHERE LOWER(platform_id) = 'reelshort' OR id LIKE 'rs_%'")
rs_count = cur.fetchone()[0]
print(f"Found {rs_count} ReelShort dramas in hongguo_dramas table.")

cur.execute("DELETE FROM hongguo_dramas WHERE LOWER(platform_id) = 'reelshort' OR id LIKE 'rs_%'")
cur.execute("DELETE FROM drama_categories WHERE drama_id LIKE 'rs_%'")
conn.commit()

cur.execute("SELECT count(*) FROM hongguo_dramas")
remaining = cur.fetchone()[0]
print(f"Removed all ReelShort dramas! Remaining dramas in database: {remaining}")

# Check platform counts
cur.execute("SELECT platform_id, count(*) FROM hongguo_dramas GROUP BY platform_id")
print("Remaining platforms in DB:", cur.fetchall())

conn.close()

# Remove data/reelshort_catalog.json
if CACHE_JSON_PATH.exists():
    CACHE_JSON_PATH.unlink()
    print("Deleted data/reelshort_catalog.json")
