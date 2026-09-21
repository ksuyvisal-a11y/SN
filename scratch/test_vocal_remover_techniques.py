import subprocess
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent.parent))
from audio_processor import get_ffmpeg_path, load_audio_safely

in_wav = "data/projects/2acd4b0b/original_audio.wav"
ffmpeg = get_ffmpeg_path()

methods = {
    "stereotools_mlev0": "stereotools=mlev=0.00:slev=1.00:phase=0",
    "lr_diff": "pan=stereo|c0=c0-c1|c1=c0-c1",
    "lr_diff_equalized": "pan=stereo|c0=c0-c1|c1=c0-c1,equalizer=f=300:t=q:w=1.5:g=-12,equalizer=f=1000:t=q:w=2.0:g=-18,equalizer=f=2200:t=q:w=2.0:g=-18,equalizer=f=3200:t=q:w=1.8:g=-14",
    "stereotools_plus_notch": "stereotools=mlev=0.00:slev=1.00:phase=0,equalizer=f=300:t=q:w=1.5:g=-12,equalizer=f=1000:t=q:w=2.0:g=-18,equalizer=f=2200:t=q:w=2.0:g=-18,equalizer=f=3200:t=q:w=1.8:g=-14",
    "bandstop_vocal": "stereotools=mlev=0.00:slev=1.00:phase=0,bandreject=f=1200:w=1800"
}

orig_seg = load_audio_safely(in_wav)
# Dialogue 1: 0.0s - 2.15s
chunk_orig = orig_seg[0:2150]
print(f"Original D#1 dBFS: {chunk_orig.dBFS:.2f}")

for name, flt in methods.items():
    out_path = f"scratch/test_{name}.wav"
    cmd = [ffmpeg, "-y", "-i", in_wav, "-af", flt, "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", out_path]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    seg = load_audio_safely(out_path)
    chunk = seg[0:2150]
    red = chunk_orig.dBFS - chunk.dBFS
    print(f"{name:25s} -> D#1 dBFS: {chunk.dBFS:.2f} (reduction: {red:.2f} dB), total dBFS: {seg.dBFS:.2f}")
