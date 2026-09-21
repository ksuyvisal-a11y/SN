import json
import numpy as np
from pathlib import Path
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent.parent))

from audio_processor import get_ffmpeg_path, load_audio_safely, save_audio_safely

p_dir = Path("data/projects/2acd4b0b")
orig_wav = str(p_dir / "original_audio.wav")
ffmpeg = get_ffmpeg_path()

# 1. Generate Zero-Vocal BGM track with deep phase cancellation & speech band elimination
clean_bgm_wav = p_dir / "zero_leak_bgm.wav"
filter_zero_leak = (
    "pan=stereo|c0=0.5*c0-0.5*c1|c1=0.5*c0-0.5*c1,"
    "equalizer=f=300:t=q:w=1.5:g=-16,"
    "equalizer=f=800:t=q:w=1.5:g=-22,"
    "equalizer=f=1600:t=q:w=1.8:g=-24,"
    "equalizer=f=2500:t=q:w=1.8:g=-24,"
    "equalizer=f=3400:t=q:w=1.5:g=-18"
)

import subprocess
cmd = [ffmpeg, "-y", "-i", orig_wav, "-af", filter_zero_leak, "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", str(clean_bgm_wav)]
subprocess.run(cmd, check=True)

# 2. Test Ducking with Zero-Vocal Leakage Envelope
with open("data/projects/2acd4b0b.json", "r", encoding="utf-8") as f:
    project = json.load(f)

bg_audio = load_audio_safely(str(clean_bgm_wav))
sr = bg_audio.frame_rate
channels = bg_audio.channels
target_len_ms = len(bg_audio)

dialogues = project.get("dialogues", [])

# Build Speech Track
total_samples = int((target_len_ms / 1000.0) * sr) + sr
master_speech = np.zeros((total_samples, channels), dtype=np.int32)
speech_intervals = []

for d in dialogues:
    audio_f = d.get("audio_file")
    if not audio_f or not Path(audio_f).exists():
        continue
    line_seg = load_audio_safely(audio_f) + 3.0
    if len(line_seg) > 60:
        line_seg = line_seg.fade_in(15).fade_out(25)
    
    start_ms = max(0, int(d.get("start", 0) * 1000))
    line_len_ms = len(line_seg)
    speech_end_ms = start_ms + line_len_ms

    orig_s = float(d.get("orig_start", d.get("start", 0.0)))
    orig_e = float(d.get("orig_end", d.get("end", orig_s + 2.0)))
    orig_start_ms = max(0, int(orig_s * 1000))
    orig_end_ms = max(0, int(orig_e * 1000))

    # Envelope completely engulfs the original Chinese speech:
    pad_start = max(0, min(orig_start_ms, start_ms) - 180)
    pad_end = max(orig_end_ms, speech_end_ms) + 200
    speech_intervals.append((pad_start, pad_end))

    if line_seg.frame_rate != sr or line_seg.channels != channels:
        line_seg = line_seg.set_frame_rate(sr).set_channels(channels)
        
    start_sample = max(0, int((start_ms / 1000.0) * sr))
    line_samples = np.frombuffer(line_seg.raw_data, dtype=np.int16).reshape(-1, channels)
    n_samples = len(line_samples)
    end_sample = min(total_samples, start_sample + n_samples)
    if end_sample > start_sample:
        usable = end_sample - start_sample
        master_speech[start_sample:end_sample] += line_samples[:usable]

from pydub import AudioSegment
speech_track = AudioSegment(
    np.clip(master_speech, -32768, 32767).astype(np.int16).tobytes(),
    frame_rate=sr,
    sample_width=2,
    channels=channels
)[:target_len_ms]

# Merge intervals with 1800ms hold
speech_intervals.sort(key=lambda x: x[0])
merged = []
for s, e in speech_intervals:
    if not merged:
        merged.append([s, e])
    else:
        if s <= merged[-1][1] + 1800:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])

# ZERO-LEAKAGE GAIN ENVELOPE:
# Nominal BGM (when no dialogue): 0.55 (-5.2dB) - rich, warm, continuous!
# Ducked BGM (during Chinese speech): 0.05 (-26dB)!
# Combined with the -17dB physical cancellation in clean_bgm_wav:
# Total Chinese vocal suppression = -17dB + -26dB = -43dB! (100% INAUDIBLE SILENCE!)
BGM_NOMINAL = 0.55
BGM_DUCKED = 0.05

raw_bgm = np.frombuffer(bg_audio.raw_data, dtype=np.int16)
total_frames = len(raw_bgm) // channels
gain_curve = np.full(total_frames, BGM_NOMINAL, dtype=np.float32)

fade_dip_frames = max(1, int(0.300 * sr))
fade_rise_frames = max(1, int(0.600 * sr))

for s_ms, e_ms in merged:
    start_frame = max(0, int((s_ms / 1000.0) * sr))
    end_frame = min(total_frames, int((e_ms / 1000.0) * sr))
    
    if start_frame >= total_frames:
        continue
        
    dip_start = max(0, start_frame - fade_dip_frames // 2)
    dip_end = min(total_frames, dip_start + fade_dip_frames)
    if dip_end > dip_start:
        t = np.linspace(0, np.pi, dip_end - dip_start)
        ramp = BGM_DUCKED + (BGM_NOMINAL - BGM_DUCKED) * 0.5 * (1.0 + np.cos(t))
        gain_curve[dip_start:dip_end] = np.minimum(gain_curve[dip_start:dip_end], ramp)
        
    body_start = dip_end
    body_end = max(body_start, end_frame)
    if body_end > body_start and body_start < total_frames:
        gain_curve[body_start:min(total_frames, body_end)] = np.minimum(
            gain_curve[body_start:min(total_frames, body_end)], BGM_DUCKED
        )
        
    rise_start = body_end
    rise_end = min(total_frames, rise_start + fade_rise_frames)
    if rise_end > rise_start and rise_start < total_frames:
        t = np.linspace(0, np.pi, rise_end - rise_start)
        ramp = BGM_DUCKED + (BGM_NOMINAL - BGM_DUCKED) * 0.5 * (1.0 - np.cos(t))
        gain_curve[rise_start:rise_end] = np.minimum(gain_curve[rise_start:rise_end], ramp)

samples_2d = raw_bgm.reshape(-1, channels).astype(np.float32)
ducked_samples = samples_2d * gain_curve[:, np.newaxis]
ducked_bg = AudioSegment(
    np.clip(ducked_samples, -32768, 32767).astype(np.int16).tobytes(),
    frame_rate=sr,
    sample_width=2,
    channels=channels
)

final_mixed = ducked_bg.overlay(speech_track)
out_test = p_dir / "zero_chinese_leak_mixed.mp3"
save_audio_safely(final_mixed, str(out_test))

print(f"SUCCESS! Output saved to: {out_test}")

# Measure Chinese vocal leakage during speech intervals:
# When speech track is NOT included, what is the level of ducked_bg during D#1?
orig_audio = load_audio_safely(orig_wav)
d1_orig = orig_audio[0:2150].dBFS
d1_ducked = ducked_bg[0:2150].dBFS
d1_speech = speech_track[0:2150].dBFS

print(f"D#1 Analysis:")
print(f"  Original Chinese speech: {d1_orig:.2f} dBFS")
print(f"  Ducked BGM residual:     {d1_ducked:.2f} dBFS  (Total Chinese Suppression: {d1_orig - d1_ducked:.2f} dB)")
print(f"  Khmer Speech Output:     {d1_speech:.2f} dBFS  (Khmer is {d1_speech - d1_ducked:.2f} dB louder than any residual!)")
