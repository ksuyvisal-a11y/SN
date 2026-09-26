from pathlib import Path

hg_dir = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader")
app_dir = hg_dir / "app"

(hg_dir / ".hg_dev").write_text("dev", encoding="utf-8")
(app_dir / ".hg_dev").write_text("dev", encoding="utf-8")

print("Created .hg_dev in:", hg_dir / ".hg_dev")
print("Created .hg_dev in:", app_dir / ".hg_dev")
