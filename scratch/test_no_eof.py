import subprocess
import time
import os
from pathlib import Path
from audio_processor import get_ffmpeg_path, get_silent_kwargs

ff = get_ffmpeg_path()
test_ep_url = 'https://play.modujx17.com/20260920/n8GveYyN/index.m3u8'
dest = Path('scratch/test_fast_ep.mp4')
if dest.exists():
    dest.unlink()

cmd = [
    ff,
    '-y',
    '-i', test_ep_url,
    '-c', 'copy',
    '-bsf:a', 'aac_adtstoasc',
    '-movflags', '+faststart',
    str(dest)
]

print("Testing FFmpeg stream copy without reconnect_at_eof...")
t0 = time.time()
proc = subprocess.run(cmd, capture_output=True, timeout=120, **get_silent_kwargs())
dt = time.time() - t0
print(f"Exited with code {proc.returncode} in {dt:.1f}s")
if dest.exists():
    print(f"File size: {dest.stat().st_size / (1024*1024):.2f} MB")
