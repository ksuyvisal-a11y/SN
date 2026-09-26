import sys
sys.stdout.reconfigure(encoding='utf-8')
import marshal
import dis
from pathlib import Path

p_server = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app\server.pyc")
with open(p_server, "rb") as f:
    f.seek(16)
    code = marshal.load(f)

for c in code.co_consts:
    if hasattr(c, "co_code") and c.co_name == "dl_submit":
        dis.dis(c)
