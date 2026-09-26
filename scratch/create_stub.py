from pathlib import Path

target = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app\server.py")
content = 'import runpy\nrunpy.run_path(__file__ + "c", run_name="__main__")\n'
target.write_text(content, encoding="utf-8")
print(f"Created {target} successfully!")
