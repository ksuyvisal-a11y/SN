import sys
sys.stdout.reconfigure(encoding='utf-8')
import dis
import marshal
from pathlib import Path

p_launcher = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\launcher.pyc")
with open(p_launcher, "rb") as f:
    f.seek(16)
    code = marshal.load(f)

# Print functions inside launcher
for c in code.co_consts:
    if hasattr(c, "co_code"):
        print(f"Function: {c.co_name}")
        for const in c.co_consts:
            if isinstance(const, str):
                print(f"  str: {const}")
