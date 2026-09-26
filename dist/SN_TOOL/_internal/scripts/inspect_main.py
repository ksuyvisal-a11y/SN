import marshal
from pathlib import Path

HG_DIR = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader")

with open(HG_DIR / "launcher.pyc", "rb") as f:
    f.seek(16)
    code = marshal.load(f)

for const in code.co_consts:
    if hasattr(const, "co_name") and const.co_name == "main":
        print("=== main consts ===")
        for c in const.co_consts:
            print(" -", repr(c))
        print("=== main names ===")
        print(const.co_names)
