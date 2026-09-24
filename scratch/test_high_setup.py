import asyncio
import os
import sys
from pathlib import Path
sys.path.insert(0, ".")

import urllib.request
import urllib.parse
import json
import edge_tts
from audio_processor import get_ffmpeg_path
import subprocess

# Patch edge_tts Communicate for 96kbitrate
def setup_high_fidelity_edge_tts():
    import edge_tts.communicate
    fp = edge_tts.communicate.__file__
    with open(fp, "r", encoding="utf-8") as f:
        src = f.read()
    if '"outputFormat":"audio-24khz-48kbitrate-mono-mp3"' in src:
        src = src.replace(
            '"outputFormat":"audio-24khz-48kbitrate-mono-mp3"',
            '"outputFormat":"audio-24khz-96kbitrate-mono-mp3"'
        )
        mod = dict(edge_tts.communicate.__dict__)
        exec(compile(src, fp, "exec"), mod)
        edge_tts.Communicate = mod["Communicate"]
        edge_tts.communicate.Communicate = mod["Communicate"]
        print("[OK] Edge-TTS upgraded to 96kbps high-fidelity stream.")

setup_high_fidelity_edge_tts()

# Test synthesize
async def test():
    comm = edge_tts.Communicate("សួស្តីបងប្អូនទាំងអស់គ្នា ពិសិដ្ឋ និង ស្រីមុំ មកដល់ហើយ", "km-KH-PisethNeural")
    raw_p = "scratch/test_high_piseth_raw.mp3"
    await comm.save(raw_p)
    
    # 48kHz mastering
    out_master = "scratch/test_high_piseth_48k.mp3"
    cmd = [
        get_ffmpeg_path(), "-y", "-i", raw_p,
        "-ar", "48000",
        "-b:a", "128k",
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        out_master
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Mastered output created:", out_master, Path(out_master).stat().st_size, "bytes")

asyncio.run(test())
