import sys
sys.stdout.reconfigure(encoding='utf-8')
import marshal
from pathlib import Path

p_hg = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app\hongguo.pyc")
with open(p_hg, "rb") as f:
    f.seek(16)
    code = marshal.load(f)

print("Names in hongguo.pyc:")
print([n for n in code.co_names if 'lic' in n.lower() or 'auth' in n.lower() or 'pay' in n.lower() or 'limit' in n.lower()])

# Check constants/strings in hongguo.pyc
def get_all_strings(co):
    res = []
    for c in co.co_consts:
        if isinstance(c, str):
            res.append(c)
        elif hasattr(c, "co_consts"):
            res.extend(get_all_strings(c))
    return res

all_s = get_all_strings(code)
print("Strings with license/limit/supabase:", [s for s in all_s if any(k in s.lower() for k in ['license', 'limit', 'supabase', 'allowed'])][:10])
