from pathlib import Path
p = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app\sign")
print("Sign dir exists:", p.exists())
if p.exists():
    for f in p.iterdir():
        print(f" - {f.name}")
