import sys
import inspect

sys.stdout.reconfigure(encoding='utf-8')
app_path = r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app"
sys.path.insert(0, app_path)

import hongguo
import offline_dl

print("hongguo.get_episodes signature:", inspect.signature(hongguo.get_episodes))
print("offline_dl.dl_series signature:", inspect.signature(offline_dl.dl_series))
print("offline_dl.dl_batch signature:", inspect.signature(offline_dl.dl_batch))
