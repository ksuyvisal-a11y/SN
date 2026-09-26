import sys
sys.stdout.reconfigure(encoding='utf-8')
import marshal
from pathlib import Path

p_lic = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app\licensing.pyc")
with open(p_lic, "rb") as f:
    f.seek(16)
    code = marshal.load(f)

print("Exported function names in licensing.pyc:")
for c in code.co_consts:
    if hasattr(c, "co_code"):
        print(f"  def {c.co_name}{c.co_varnames[:c.co_argcount]}:")
