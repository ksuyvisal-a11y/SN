import urllib.request
import json

# Start server if needed
import subprocess, time, socket

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(('127.0.0.1', port)) == 0

if not is_port_open(8000):
    cmd = 'cmd.exe /c "set PYTHONIOENCODING=utf-8&& set PYTHONUTF8=1&& cd /d C:\\Users\\TUF\\AppData\\Local\\Programs\\Hongguo Downloader&& python\\python.exe launcher.pyc"'
    subprocess.Popen(cmd, shell=True)
    for _ in range(30):
        if is_port_open(8000):
            print("Server is UP!")
            break
        time.sleep(1)

# Check GET /dl/config
try:
    with urllib.request.urlopen("http://127.0.0.1:8000/dl/config", timeout=5) as res:
        cfg = json.loads(res.read().decode('utf-8'))
        print("Current config:", cfg)
except Exception as e:
    print("GET config error:", e)

# Test POST /dl/config to change output_dir to D:/SN_Dramas
try:
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request("http://127.0.0.1:8000/dl/config", data=json.dumps({"output_dir": "D:/SN_Dramas"}).encode('utf-8'), headers=headers)
    with urllib.request.urlopen(req, timeout=5) as res:
        res_data = json.loads(res.read().decode('utf-8'))
        print("POST config result:", res_data)
except Exception as e:
    print("POST config error:", e)
