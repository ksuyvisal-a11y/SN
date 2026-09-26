import sys
import os

# Use UTF-8
sys.stdout.reconfigure(encoding='utf-8')

app_path = r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app"
sys.path.insert(0, app_path)

os.environ["SIGN_SERVER"] = "http://127.0.0.1:9099"
os.environ["PORT"] = "8000"
os.environ["BIND_HOST"] = "127.0.0.1"

import server

print("Server module:", server)
if hasattr(server, "app"):
    app = server.app
    print("FastAPI app:", app)
    print("\nRegistered routes:")
    for route in app.routes:
        print(f" - {route.path} [{','.join(getattr(route, 'methods', []))}]")
else:
    print("No 'app' attribute found! Attributes:", dir(server))
