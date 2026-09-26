import dis
import marshal
from pathlib import Path

def inspect_pyc(path):
    print(f"=== Inspecting {path.name} ===")
    with open(path, "rb") as f:
        # Magic (4), flags (4), timestamp (4), size (4) in py 3.11+
        f.seek(16)
        code = marshal.load(f)
    print("Code name:", code.co_name)
    print("Consts (strings):", [c for c in code.co_consts if isinstance(c, str)][:20])
    print("Names:", list(code.co_names)[:25])

p_launcher = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\launcher.pyc")
inspect_pyc(p_launcher)

p_server = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app\server.pyc")
inspect_pyc(p_server)
