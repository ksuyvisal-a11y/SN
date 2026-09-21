import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from audio_processor import load_audio_safely

p = Path("data/projects/2acd4b0b")
orig = load_audio_safely(str(p / "original_audio.wav"))
bgm = load_audio_safely(str(p / "original_audio_bgm.wav"))

# Let's inspect stereo difference in orig
orig_samples = np.frombuffer(orig.raw_data, dtype=np.int16).reshape(-1, orig.channels)
print(f"Orig channels: {orig.channels}, sample count: {len(orig_samples)}")
if orig.channels == 2:
    diff = np.abs(orig_samples[:, 0].astype(np.float32) - orig_samples[:, 1].astype(np.float32))
    print(f"Mean L-R absolute diff: {np.mean(diff):.2f}, Max L-R: {np.max(diff):.2f}")
    zero_diff_pct = (diff < 10).mean() * 100
    print(f"Percentage where L ~ R (mono): {zero_diff_pct:.1f}%")

bgm_samples = np.frombuffer(bgm.raw_data, dtype=np.int16).reshape(-1, bgm.channels)
# check rms every 100ms
sr = bgm.frame_rate
chunk_size = sr // 10 # 100ms
rms_list = []
for i in range(0, len(bgm_samples) - chunk_size, chunk_size):
    chunk = bgm_samples[i:i+chunk_size]
    rms = np.sqrt(np.mean(chunk.astype(np.float32)**2))
    rms_list.append(rms)

rms_arr = np.array(rms_list)
print(f"BGM RMS min: {rms_arr.min():.2f}, median: {np.median(rms_arr):.2f}, max: {rms_arr.max():.2f}")
print(f"BGM quiet chunks (< 50 RMS): {(rms_arr < 50).mean()*100:.1f}%")
print(f"BGM very quiet chunks (< 10 RMS): {(rms_arr < 10).mean()*100:.1f}%")
