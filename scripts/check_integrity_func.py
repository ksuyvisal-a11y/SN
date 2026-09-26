import sys
import marshal
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

pyc = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app\server.pyc")
with open(pyc, "rb") as f:
    f.seek(16)
    code = marshal.load(f)

print("server.pyc first 40 names:", code.co_names[:40])

# Check what _verify_integrity does in server.pyc
for const in code.co_consts:
    if hasattr(const, "co_name") and const.co_name == "_verify_integrity":
        print("=== _verify_integrity consts ===")
        print(const.co_consts)
        print("=== _verify_integrity names ===")
        print(const.co_names)
