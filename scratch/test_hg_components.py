import os
import sys
import time
import socket
import subprocess
import urllib.request
import json
from pathlib import Path

HG_ROOT = Path(r"C:\Users\TUF\AppData\Local\Programs\Hongguo Downloader")
JAVA_BIN = HG_ROOT / "jre" / "bin" / "java.exe"
JAR_PATH = HG_ROOT / "app" / "sign" / "unidbg-sign.jar"
PYTHON_BIN = HG_ROOT / "python" / "python.exe"
SERVER_PY = HG_ROOT / "app" / "server.pyc"

print(f"Java exists: {JAVA_BIN.exists()}")
print(f"Jar exists: {JAR_PATH.exists()}")
print(f"Python exists: {PYTHON_BIN.exists()}")
print(f"Server pyc exists: {SERVER_PY.exists()}")

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(('127.0.0.1', port)) == 0

print(f"Signer port 9099 open: {is_port_open(9099)}")
print(f"Server port 8000 open: {is_port_open(8000)}")
