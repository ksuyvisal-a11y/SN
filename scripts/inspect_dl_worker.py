import sys
import marshal
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
pyc = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app\server.pyc")
with open(pyc, "rb") as f:
    f.seek(16)
    code = marshal.load(f)

for const in code.co_consts:
    if hasattr(const, "co_name") and const.co_name == "_dl_worker":
        print("=== _dl_worker ===")
        print("names:", const.co_names)
        print("varnames:", const.co_varnames)
        print("consts:", const.co_consts)
