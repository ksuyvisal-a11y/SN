import urllib.request
import urllib.parse
import json

# Test 1: Let's test the free web endpoint /TextToMp3Add with minimal params
url = "https://speechgen.io/index.php?r=tts/TextToMp3Add&lang=km-KH"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "Referer": "https://speechgen.io/en/tts-khmer/",
    "Origin": "https://speechgen.io",
    "Content-Type": "application/x-www-form-urlencoded"
}

payload = {
    "lang": "km-KH",
    "voice": "Piseth",
    "style": "",
    "speed": 1,
    "pitch": 0,
    "volume": 100,
    "format": "mp3",
    "pp": 400,
    "ps": 0,
    "hz": 48000,
    "speed_type": 1,
    "bitrate": 128,
    "channels": 1,
    "text": "សួស្តីបងប្អូនទាំងអស់គ្នា",
    "captcha_value": "",
    "vocabulary": False,
    "popup_cptch": ""
}

data = urllib.parse.urlencode({"param": json.dumps(payload)}).encode("utf-8")
req = urllib.request.Request(url, data=data, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        res = resp.read().decode("utf-8")
        print("Response from TextToMp3Add:", res)
except Exception as e:
    print("Error calling TextToMp3Add:", e)

# Test 2: Test official API without token to see error message
api_url = "https://speechgen.io/index.php?r=api/text"
api_payload = {
    "token": "test",
    "email": "test@gmail.com",
    "voice": "Piseth",
    "text": "សួស្តី"
}
req2 = urllib.request.Request(api_url, data=urllib.parse.urlencode(api_payload).encode("utf-8"), headers=headers)
try:
    with urllib.request.urlopen(req2, timeout=10) as resp2:
        res2 = resp2.read().decode("utf-8")
        print("Response from API:", res2)
except Exception as e:
    print("Error calling API:", e)
