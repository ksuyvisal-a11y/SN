import sys
import marshal
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

pyc = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app\server.pyc")
with open(pyc, "rb") as f:
    f.seek(16)
    code = marshal.load(f)

for const in code.co_consts:
    if hasattr(const, "co_name"):
        print("Function:", const.co_name, "names:", const.co_names[:10])
