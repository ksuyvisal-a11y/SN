import sys
import sqlite3

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect("data/hongguo_catalog.db")
c = conn.cursor()
c.execute("SELECT id, title_cn, platform_id, total_episodes FROM hongguo_dramas WHERE platform_id='hongguo' LIMIT 5")
for r in c.fetchall():
    print(r)

# Check 东北话事人 in database
c.execute("SELECT id, title_cn, platform_id, total_episodes FROM hongguo_dramas WHERE title_cn LIKE '%东北话事人%'")
print("\n东北话事人 in DB:")
for r in c.fetchall():
    print(r)
