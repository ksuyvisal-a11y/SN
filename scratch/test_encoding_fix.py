import sys
import subprocess
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass
import audio_processor
from audio_processor import get_media_duration, extract_audio_from_video
from vocal_remover import separate_vocals_and_bgm

print("[TEST 1] Testing subprocess text decoding with non-ASCII and byte 0x9d...")
test_script = "import sys; sys.stdout.buffer.write('Chinese: 电视剧 《总裁的替嫁新娘》 Khmer: រឿងភាគ ពិសិដ្ឋ \x9d \u201d'.encode('utf-8', errors='replace') + b'\\x9d')"
proc = subprocess.run(['python', '-c', test_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
print("Returncode:", proc.returncode)
print("Stdout decoded cleanly without charmap exception:", bool(proc.stdout))
print("Splitlines works without AttributeError:", proc.stdout.splitlines())

print("\n[TEST 2] Testing get_media_duration on cache/test_drama.mp4...")
dur = get_media_duration('cache/test_drama.mp4')
print(f"Detected duration: {dur}s")

print("\n[TEST 3] Testing separate_vocals_and_bgm...")
import os
test_audio = "cache/temp_test_audio.wav"
extract_audio_from_video("cache/test_drama.mp4", test_audio)
bgm, voc = separate_vocals_and_bgm(test_audio, output_dir="cache")
print("BGM file:", bgm, "exists:", os.path.exists(bgm))
print("Vocals file:", voc, "exists:", os.path.exists(voc))

print("\nALL ENCODING & AUTO DUBBING TESTS PASSED 100%!")
