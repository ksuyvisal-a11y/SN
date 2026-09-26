import sys
import marshal
from pathlib import Path

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

HG_DIR = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader")

with open(HG_DIR / "launcher.pyc", "rb") as f:
    f.seek(16)
    code = marshal.load(f)

for const in code.co_consts:
    if hasattr(const, "co_name") and const.co_name == "main":
        print("=== main consts ===")
        for idx, c in enumerate(const.co_consts):
            print(f" {idx}: {repr(c)}")
        print("\n=== main names ===")
        print(const.co_names)
