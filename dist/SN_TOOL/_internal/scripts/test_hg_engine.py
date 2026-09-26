import os
import sys
import subprocess
from pathlib import Path

HG_DIR = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader")
print("HG_DIR exists:", HG_DIR.exists())
if HG_DIR.exists():
    for item in HG_DIR.iterdir():
        print(f" - {item.name} ({'dir' if item.is_dir() else 'file'})")

app_dir = HG_DIR / "app"
if app_dir.exists():
    print("\nFiles in app:")
    for item in app_dir.iterdir():
        print(f" - {item.name}")
