import sys
sys.stdout.reconfigure(encoding='utf-8')
import marshal
import dis
from pathlib import Path

p_launcher = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\launcher.pyc")
with open(p_launcher, "rb") as f:
    f.seek(16)
    code = marshal.load(f)

for c in code.co_consts:
    if hasattr(c, "co_code") and c.co_name == "main":
        # Disassemble only first 600 instructions
        instrs = list(dis.get_instructions(c))
        for ins in instrs:
            if ins.starts_line and ins.starts_line > 135:
                break
            print(f"{ins.starts_line or ''} {ins.opname} {ins.argval}")
