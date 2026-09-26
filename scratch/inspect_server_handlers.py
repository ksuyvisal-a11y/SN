import sys
sys.stdout.reconfigure(encoding='utf-8')
import marshal
from pathlib import Path

p_server = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app\server.pyc")
with open(p_server, "rb") as f:
    f.seek(16)
    code = marshal.load(f)

for c in code.co_consts:
    if hasattr(c, "co_code"):
        name = c.co_name
        if any(k in name for k in ['dl_', 'submit', 'resolve', 'episodes', 'download']):
            print(f"Handler: {name}, args: {c.co_varnames[:c.co_argcount]}")
            # check strings in this function
            strs = [s for s in c.co_consts if isinstance(s, str)]
            print("  strings:", strs[:10])
