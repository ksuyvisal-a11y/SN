import os
from pathlib import Path

for root in [r"D:\SN_Dramas", r"C:\SN_Dramas", str(Path.home() / "Videos" / "Hongguo")]:
    p = Path(root)
    if p.exists():
        print(f"Directory {root}:")
        for f in p.rglob("*"):
            if f.is_file():
                print(f" - {f} ({f.stat().st_size / (1024*1024):.2f} MB)")
