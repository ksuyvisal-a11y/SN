import sys
sys.stdout.reconfigure(encoding='utf-8')
import dis
import marshal
from pathlib import Path

def extract_strings(code_obj):
    strs = []
    for c in code_obj.co_consts:
        if isinstance(c, str):
            strs.append(c)
        elif hasattr(c, "co_consts"):
            strs.extend(extract_strings(c))
    return strs

p_server = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app\server.pyc")
with open(p_server, "rb") as f:
    f.seek(16)
    code = marshal.load(f)

all_s = extract_strings(code)
routes = [s for s in all_s if s.startswith("/api/") or s.startswith("/")]
print("Unique routes/endpoints found in server.pyc:")
for r in sorted(set(routes)):
    if len(r) < 60 and not " " in r and r.count("/") >= 2:
        print(" ", r)
