import sys
sys.stdout.reconfigure(encoding='utf-8')
import marshal
import dis
from pathlib import Path

p_server = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app\server.pyc")
with open(p_server, "rb") as f:
    f.seek(16)
    code = marshal.load(f)

# Find instructions near the end of code
instrs = list(dis.get_instructions(code))
print(f"Total instructions in module: {len(instrs)}")
for ins in instrs[-100:]:
    print(f"{ins.starts_line or ''} {ins.opname} {ins.argval}")
