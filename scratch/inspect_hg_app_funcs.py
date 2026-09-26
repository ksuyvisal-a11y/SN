import sys
sys.stdout.reconfigure(encoding='utf-8')
import marshal
from pathlib import Path

def inspect_file(pyc_path):
    print(f"\n==========================================")
    print(f"File: {pyc_path.name}")
    with open(pyc_path, "rb") as f:
        f.seek(16)
        code = marshal.load(f)
    for c in code.co_consts:
        if hasattr(c, "co_code"):
            # function or class
            print(f"Function/Class: {c.co_name}, args: {c.co_varnames[:c.co_argcount]}")

HG_APP = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app")
inspect_file(HG_APP / "downloader.pyc")
inspect_file(HG_APP / "hongguo.pyc")
