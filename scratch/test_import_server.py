import os
import sys
import traceback

sys.path.insert(0, r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader\app")
os.environ["SIGN_SERVER"] = "http://127.0.0.1:9099"
os.environ["PORT"] = "8000"
os.environ["BIND_HOST"] = "127.0.0.1"
os.environ["HG_OUT"] = "D:/SN_Dramas"

print("Importing server...")
try:
    import server
    print("Server imported successfully!")
    print("App object:", getattr(server, "app", None))
except Exception as e:
    print("Exception on import server:")
    traceback.print_exc()
