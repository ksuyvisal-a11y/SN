import sys, yt_dlp
sys.stdout.reconfigure(encoding='utf-8')
q = '全家把我当乡下老太，都吓傻了'
ydl_opts = {'quiet': True, 'extract_flat': True}
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(f"ytsearch5:{q}", download=False)
    entries = info.get('entries', [])
    print(f"Found {len(entries)} entries:")
    for idx, e in enumerate(entries):
        print(f"{idx+1}: title='{e.get('title')}' | duration={e.get('duration')} | id={e.get('id')}")
