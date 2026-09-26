from pathlib import Path
p = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app\config.json")
if p.exists():
    print(p.read_text(encoding="utf-8", errors="ignore"))
