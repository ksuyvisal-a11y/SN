import sys
import marshal
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HG_DIR = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader")

with open(HG_DIR / "launcher.pyc", "rb") as f:
    f.seek(16)
    code = marshal.load(f)

for const in code.co_consts:
    if hasattr(const, "co_name") and const.co_name == "_spawn":
        print("=== _spawn ===")
        print("names:", const.co_names)
        print("varnames:", const.co_varnames)
        print("consts:", const.co_consts)
