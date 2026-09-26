import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
app_path = r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app"
sys.path.insert(0, app_path)

import hongguo
import offline_dl

print("hongguo attributes:", dir(hongguo))
print("\noffline_dl attributes:", dir(offline_dl))
