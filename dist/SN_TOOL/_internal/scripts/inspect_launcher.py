import dis
import marshal
from pathlib import Path

HG_DIR = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader")

def inspect_pyc(p):
    with open(p, "rb") as f:
        f.seek(16) # Skip header for Python 3.7+
        code = marshal.load(f)
    print(f"\n--- Code object in {p.name} ---")
    print("Co_names:", code.co_names)
    print("Co_consts (strings only):", [c for c in code.co_consts if isinstance(c, str)])

try:
    inspect_pyc(HG_DIR / "launcher.pyc")
except Exception as e:
    print("launcher.pyc error:", e)

try:
    with open(HG_DIR / "app" / "server.py", "r", encoding="utf-8") as f:
        print("\n--- app/server.py contents ---")
        print(f.read())
except Exception as e:
    print("server.py error:", e)
