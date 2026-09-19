import urllib.request
import json

url = "http://127.0.0.1:8000/api/story-config"

# Test GET
req = urllib.request.Request(url)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    print("GET STATUS:", data.get("success"), "CONFIG:", data.get("config"))

# Test POST with new ducking and speech values
new_cfg = {
    "khmer_voice": "piseth",
    "auto_multi_voice": False,
    "source_lang": "auto",
    "whisper_model": "medium",
    "aspect_ratio": "9:16",
    "subtitle_mode": "none",
    "dubbing_mode": "smart_bgm",
    "ducking_volume": "0.15",
    "speech_boost_db": 2.5
}

post_data = json.dumps(new_cfg).encode('utf-8')
post_req = urllib.request.Request(url, data=post_data, headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(post_req) as resp:
    res = json.loads(resp.read().decode())
    print("POST STATUS:", res.get("success"), "CONFIG:", res.get("config"))
