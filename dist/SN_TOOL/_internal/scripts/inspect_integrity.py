import sys
import marshal
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

pyc = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app\_integrity.pyc")
if pyc.exists():
    with open(pyc, "rb") as f:
        f.seek(16)
        code = marshal.load(f)
    print("_integrity.pyc names:", code.co_names)
    print("_integrity.pyc consts:", [c for c in code.co_consts if isinstance(c, (str, int))])
