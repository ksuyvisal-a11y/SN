import marshal
from pathlib import Path

pyc = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app\server.pyc")
with open(pyc, "rb") as f:
    f.seek(16)
    code = marshal.load(f)

print("server.pyc names:", code.co_names[:30])
print("server.pyc consts strings:", [c for c in code.co_consts if isinstance(c, str)][:30])
