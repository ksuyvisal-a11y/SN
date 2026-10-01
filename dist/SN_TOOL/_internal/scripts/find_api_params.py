import urllib.request
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
headers = {'User-Agent': 'Mozilla/5.0'}
url = 'https://www.reelshort.com/_next/static/chunks/pages/_app-2c9087032d279f25.js'
with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as cr:
    code = cr.read().decode('utf-8', errors='ignore')

pos = code.find('17150:function')
print(code[pos:pos+1500])
