import os
import sys
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from audio_processor import load_audio_safely, save_audio_safely, get_ffmpeg_path

# Let's test on data/projects/2acd4b0b/original_audio.wav
p = Path("data/projects/2acd4b0b")
orig_wav = p / "original_audio.wav"

if not orig_wav.exists():
    print("Original audio not found")
    sys.exit(1)

# Test 1: Better BGM extraction filter
# Keep bass (f < 160Hz) in both channels, apply gentle center reduction for vocal band
# so the song's beat, bass, melody, and stereo ambience are preserved!
test_bgm_out = p / "test_improved_bgm.wav"
ffmpeg = get_ffmpeg_path()

# Modern FFmpeg vocal suppression preserving bass and stereo sides:
# stereotools reduces mid (center mono speech) while keeping side 100% stereo music,
# plus gentle vocal notch
cmd_better_bgm = [
    ffmpeg, "-y",
    "-i", str(orig_wav),
    "-af", "stereotools=mlev=0.20:slev=1.00:phase=0,equalizer=f=1000:t=q:w=1.2:g=-6,equalizer=f=2500:t=q:w=1.2:g=-5",
    "-acodec", "pcm_s16le",
    "-ar", "44100",
    "-ac", "2",
    str(test_bgm_out)
]
import subprocess
subprocess.run(cmd_better_bgm, check=True)

seg_orig = load_audio_safely(str(orig_wav))
seg_old_bgm = load_audio_safely(str(p / "original_audio_bgm.wav"))
seg_new_bgm = load_audio_safely(str(test_bgm_out))

print(f"Original: dBFS={seg_orig.dBFS:.2f}")
print(f"Old BGM : dBFS={seg_old_bgm.dBFS:.2f}")
print(f"New BGM : dBFS={seg_new_bgm.dBFS:.2f}")
