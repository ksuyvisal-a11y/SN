import json
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from audio_processor import load_audio_safely, save_audio_safely, enhance_voice_clarity_studio

p_dir = Path("data/projects/2acd4b0b")
with open("data/projects/2acd4b0b.json", "r", encoding="utf-8") as f:
    project = json.load(f)

# Use the improved BGM track (test_improved_bgm.wav) or isolated_bgm_file
bgm_path = p_dir / "test_improved_bgm.wav"
if not bgm_path.exists():
    bgm_path = p_dir / "original_audio_bgm.wav"

bg_audio = load_audio_safely(str(bgm_path))
target_fr = bg_audio.frame_rate
channels = bg_audio.channels
target_len_ms = len(bg_audio)

dialogues = project.get("dialogues", [])
print(f"Total dialogues: {len(dialogues)}, BGM duration: {target_len_ms/1000.0:.2f}s")

# 1. Assemble Speech Track with enhancement
total_samples = int((target_len_ms / 1000.0) * target_fr) + target_fr
master_speech = np.zeros((total_samples, channels), dtype=np.int32)

speech_intervals = []
for d in dialogues:
    audio_f = d.get("audio_file")
    if not audio_f or not Path(audio_f).exists():
        continue
    
    line_seg = load_audio_safely(audio_f)
    line_seg = line_seg + 3.0 # +3dB clarity
    if len(line_seg) > 60:
        line_seg = line_seg.fade_in(15).fade_out(25)
        
    start_ms = max(0, int(d.get("start", 0) * 1000))
    line_dur_ms = len(line_seg)
    speech_end_ms = start_ms + line_dur_ms
    
    # Save interval with hold
    speech_intervals.append((max(0, start_ms - 100), speech_end_ms + 150))
    
    if line_seg.frame_rate != target_fr or line_seg.channels != channels:
        line_seg = line_seg.set_frame_rate(target_fr).set_channels(channels)
        
    start_sample = max(0, int((start_ms / 1000.0) * target_fr))
    line_samples = np.frombuffer(line_seg.raw_data, dtype=np.int16).reshape(-1, channels)
    n_samples = len(line_samples)
    end_sample = min(total_samples, start_sample + n_samples)
    if end_sample > start_sample:
        usable = end_sample - start_sample
        master_speech[start_sample:end_sample] += line_samples[:usable]

master_speech = np.clip(master_speech, -32768, 32767).astype(np.int16)
from pydub import AudioSegment
speech_track = AudioSegment(
    master_speech.tobytes(),
    frame_rate=target_fr,
    sample_width=2,
    channels=channels
)[:target_len_ms]

# 2. Smooth Musical BGM Gain Envelope
# Nominal BGM volume = 0.60 (sweet, pleasant background music)
# Ducked BGM volume = 0.42 (gentle dip -3dB during speech)
# Hold gap = 2500ms (so pauses between speech lines don't pump!)
speech_intervals.sort(key=lambda x: x[0])
merged_intervals = []
for s, e in speech_intervals:
    if not merged_intervals:
        merged_intervals.append([s, e])
    else:
        if s <= merged_intervals[-1][1] + 2500: # 2.5s hold
            merged_intervals[-1][1] = max(merged_intervals[-1][1], e)
        else:
            merged_intervals.append([s, e])

print(f"Merged continuous intervals: {len(merged_intervals)}")
for idx, (s, e) in enumerate(merged_intervals):
    print(f"  Speech block {idx+1}: {s/1000.0:.2f}s -> {e/1000.0:.2f}s")

raw_bgm = np.frombuffer(bg_audio.raw_data, dtype=np.int16)
total_frames = len(raw_bgm) // channels

# Nominal BGM level: 0.62 (-4dB)
# Ducked BGM level: 0.44 (-7dB)
BGM_NOMINAL = 0.62
BGM_DUCKED = 0.44

gain_curve = np.full(total_frames, BGM_NOMINAL, dtype=np.float32)

fade_dip_frames = max(1, int(0.400 * target_fr))  # 400ms smooth dip
fade_rise_frames = max(1, int(0.800 * target_fr)) # 800ms gentle return

for s_ms, e_ms in merged_intervals:
    start_frame = max(0, int((s_ms / 1000.0) * target_fr))
    end_frame = min(total_frames, int((e_ms / 1000.0) * target_fr))
    
    if start_frame >= total_frames:
        continue
        
    dip_start = max(0, start_frame - fade_dip_frames // 2)
    dip_end = min(total_frames, dip_start + fade_dip_frames)
    if dip_end > dip_start:
        # Smooth S-curve / cosine ramp
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
ducked_int16 = np.clip(ducked_samples, -32768, 32767).astype(np.int16)

ducked_bg = AudioSegment(
    ducked_int16.tobytes(),
    frame_rate=target_fr,
    sample_width=2,
    channels=channels
)

final_mixed = ducked_bg.overlay(speech_track)
out_test_mix = p_dir / "test_smooth_master_mix.mp3"
save_audio_safely(final_mixed, str(out_test_mix))

print(f"SUCCESS! Rendered {out_test_mix}")
print(f"Final Mixed: dBFS={final_mixed.dBFS:.2f}, max_dBFS={final_mixed.max_dBFS:.2f}")
print(f"Gain min={gain_curve.min():.2f}, max={gain_curve.max():.2f}")
