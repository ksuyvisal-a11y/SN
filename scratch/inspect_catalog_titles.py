import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')
sys.path.insert(0, 'data')
import hongguo_db

dramas, total = hongguo_db.query_dramas(limit=25)
print(f"Total dramas in DB: {total}")
for i, d in enumerate(dramas):
    t = d.get('title')
    cn = d.get('title_cn')
    sid = d.get('series_id')
    print(f"{i+1:02d}: id={d.get('id')} | sid={sid} | title={t} | cn={cn}")
