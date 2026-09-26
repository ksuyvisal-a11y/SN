import os
from pathlib import Path

app_dir = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader")
if app_dir.exists():
    print("Files/Dirs in app_dir:")
    for item in app_dir.iterdir():
        print(" ", item.name, "(dir)" if item.is_dir() else f"({item.stat().st_size} bytes)")
        
    # Search for python scripts or resources
    resources_dir = app_dir / "resources"
    if resources_dir.exists():
        print("\nIn resources:")
        for item in resources_dir.iterdir():
            print(" ", item.name, "(dir)" if item.is_dir() else f"({item.stat().st_size} bytes)")
else:
    print("App dir does not exist")
