from pathlib import Path

target = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app\server.py")
content = '''import sys
import os
import importlib.util

pyc_path = os.path.splitext(__file__)[0] + ".pyc"
spec = importlib.util.spec_from_file_location("server", pyc_path)
mod = importlib.util.module_from_spec(spec)
sys.modules["server"] = mod
spec.loader.exec_module(mod)

for k, v in mod.__dict__.items():
    if not k.startswith("__"):
        globals()[k] = v

app = getattr(mod, "app", None)

if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("BIND_HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting Hongguo Engine uvicorn on {host}:{port}...", flush=True)
    uvicorn.run(app, host=host, port=port)
'''
target.write_text(content, encoding="utf-8")
print("Updated server.py stub successfully!")
