import os
from pathlib import Path

app_dir = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app")
if app_dir.exists():
    print("Files/Dirs in app:")
    for item in app_dir.iterdir():
        print(" ", item.name, "(dir)" if item.is_dir() else f"({item.stat().st_size} bytes)")
