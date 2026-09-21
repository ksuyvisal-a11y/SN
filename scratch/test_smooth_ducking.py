import json
import math
import numpy as np
import time
from pathlib import Path
from pydub import AudioSegment
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from audio_processor import load_audio_safely

def apply_smooth_cinema_ducking(
    bg_audio: AudioSegment,
    speech_intervals: list,
    ducking_volume_factor: float = 0.35,  # -9dB: warm continuous BGM bed
    hold_gap_ms: int = 1800,              # Hold across 1.8s conversation pauses
    fade_in_ms: int = 300,               # 300ms smooth dip
    fade_out_ms: int = 500               # 500ms smooth return
) -> AudioSegment:
    """
    Applies continuous, sample-accurate, zero-pumping cinematic audio ducking.
    Never mutes to pure silence; maintains a continuous musical bed.
    """
    if not speech_intervals:
        return bg_audio

    # Sort and merge intervals with conversation hold
    intervals = sorted(speech_intervals, key=lambda x: x[0])
    merged = []
    for s, e in intervals:
        if not merged:
            merged.append([s, e])
        else:
            if s <= merged[-1][1] + hold_gap_ms:
                merged[-1][1] = max(merged[-1][1], e)
            else:
                merged.append([s, e])

    # Convert bg_audio to numpy buffer
    sr = bg_audio.frame_rate
    channels = bg_audio.channels
    raw_samples = np.frombuffer(bg_audio.raw_data, dtype=np.int16)
    total_frames = len(raw_samples) // channels

    # Calculate gain curve across all frames
    # Default: 1.0 (full volume)
    # Ducked: target_gain (e.g. 0.35 = -9dB, or clamped between 0.18 and 0.70)
    # Clamp ducking_volume_factor to healthy range: min 0.15 (-16dB), max 0.65 (-3.7dB)
    target_gain = float(np.clip(ducking_volume_factor, 0.15, 0.65))

    gain_curve = np.ones(total_frames, dtype=np.float32)

    fade_in_frames = max(1, int((fade_in_ms / 1000.0) * sr))
    fade_out_frames = max(1, int((fade_out_ms / 1000.0) * sr))

    for s_ms, e_ms in merged:
        start_frame = max(0, int((s_ms / 1000.0) * sr))
        end_frame = min(total_frames, int((e_ms / 1000.0) * sr))

        if start_frame >= total_frames:
            continue

        # Fade in (volume dropping from 1.0 down to target_gain)
        dip_start = max(0, start_frame - fade_in_frames // 2)
        dip_end = min(total_frames, dip_start + fade_in_frames)
        if dip_end > dip_start:
            ramp_down = np.linspace(1.0, target_gain, dip_end - dip_start, dtype=np.float32)
            gain_curve[dip_start:dip_end] = np.minimum(gain_curve[dip_start:dip_end], ramp_down)

        # Body (steady ducked level during dialogue)
        body_start = dip_end
        body_end = max(body_start, end_frame)
        if body_end > body_start and body_start < total_frames:
            gain_curve[body_start:min(total_frames, body_end)] = np.minimum(
                gain_curve[body_start:min(total_frames, body_end)], target_gain
            )

        # Fade out (volume rising from target_gain back up to 1.0)
        rise_start = body_end
        rise_end = min(total_frames, rise_start + fade_out_frames)
        if rise_end > rise_start and rise_start < total_frames:
            ramp_up = np.linspace(target_gain, 1.0, rise_end - rise_start, dtype=np.float32)
            gain_curve[rise_start:rise_end] = np.minimum(gain_curve[rise_start:rise_end], ramp_up)

    # Reshape samples and apply gain envelope
    if channels > 1:
        samples_2d = raw_samples.reshape(-1, channels).astype(np.float32)
        ducked_samples = samples_2d * gain_curve[:, np.newaxis]
    else:
        ducked_samples = raw_samples.astype(np.float32) * gain_curve

    ducked_int16 = np.clip(ducked_samples, -32768, 32767).astype(np.int16)

    return AudioSegment(
        ducked_int16.tobytes(),
        frame_rate=sr,
        sample_width=2,
        channels=channels
    )

if __name__ == "__main__":
    t0 = time.time()
    bg = load_audio_safely("data/projects/84995c0c/original_audio_bgm.wav")
    with open("data/projects/84995c0c.json", "r", encoding="utf-8") as f:
        proj = json.load(f)

    intervals = [(int(d["start"]*1000), int(d["end"]*1000)) for d in proj["dialogues"]]
    ducked = apply_smooth_cinema_ducking(bg, intervals, ducking_volume_factor=0.35)
    print(f"Smooth cinema ducking computed in {time.time() - t0:.2f}s!")
    print(f"Ducked dBFS: {ducked.dBFS:.1f} (Original: {bg.dBFS:.1f})")

    # Check 15 chunks
    for sec in range(15):
        orig_ch = bg[sec*1000:(sec+1)*1000]
        duck_ch = ducked[sec*1000:(sec+1)*1000]
        print(f"Sec {sec:2d}-{sec+1:2d}: Orig={orig_ch.dBFS:.1f}dBFS -> Ducked={duck_ch.dBFS:.1f}dBFS (Diff: {duck_ch.dBFS - orig_ch.dBFS:.1f}dB)")
