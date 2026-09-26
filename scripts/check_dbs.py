import sqlite3
from pathlib import Path

for db_p in [Path("data/hongguo_catalog.db"), Path("hongguo_db.sqlite")]:
    if db_p.exists():
        print(f"\nDB: {db_p} (size: {db_p.stat().st_size / (1024*1024):.2f} MB)")
        conn = sqlite3.connect(str(db_p))
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in c.fetchall()]
        print("Tables:", tables)
        for t in tables:
            c.execute(f"SELECT COUNT(*) FROM {t}")
            cnt = c.fetchone()[0]
            print(f" - {t}: {cnt} rows")
            c.execute(f"PRAGMA table_info({t})")
            cols = [r[1] for r in c.fetchall()]
            print(f"   columns: {cols}")
            c.execute(f"SELECT * FROM {t} LIMIT 1")
            first = c.fetchone()
            print(f"   sample: {first}")
