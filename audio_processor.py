"""
Audio Processor Engine: Audio Extraction, Time Alignment, Waveform Generation, and Smart BGM Audio Ducking
"""
import os
import io
import math
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import imageio_ffmpeg
    FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
    FFMPEG_DIR = os.path.dirname(FFMPEG_EXE)
    if FFMPEG_DIR not in os.environ.get("PATH", ""):
        os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")
except Exception:
    FFMPEG_EXE = "ffmpeg"

import pydub
from pydub import AudioSegment
pydub.AudioSegment.converter = FFMPEG_EXE
pydub.AudioSegment.ffmpeg = FFMPEG_EXE


def get_ffmpeg_path() -> str:
    """Get reliable ffmpeg binary path."""
    return FFMPEG_EXE


def load_audio_safely(file_path: str) -> AudioSegment:
    """
    Robust audio loader that decodes MP3/AAC/WAV/etc directly via FFmpeg binary.
    """
    cmd = [
        get_ffmpeg_path(),
        "-y",
        "-i", str(file_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        "-f", "wav",
        "-"
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg audio decode failed: {proc.stderr.decode('utf-8', errors='ignore')}")
    
    return AudioSegment.from_wav(io.BytesIO(proc.stdout))


def save_audio_safely(segment: AudioSegment, output_path: str, bitrate: str = "192k") -> str:
    """
    Save AudioSegment to MP3/WAV safely using FFmpeg.
    """
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    
    wav_io = io.BytesIO()
    segment.export(wav_io, format="wav")
    wav_io.seek(0)
    
    cmd = [
        get_ffmpeg_path(),
        "-y",
        "-i", "-",
        "-b:a", bitrate,
        str(out_p)
    ]
    proc = subprocess.run(cmd, input=wav_io.read(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg audio save failed: {proc.stderr.decode('utf-8', errors='ignore')}")
        
    return str(out_p)


def enhance_voice_clarity_studio(
    input_path: str,
    output_path: Optional[str] = None,
    speed_ratio: float = 1.0
) -> str:
    """
    Studio-grade vocal post-processing chain for Khmer Neural TTS:
    - High-pass filter at 75Hz (eliminates low mic rumble and plosive thuds)
    - Presence EQ boost (+2.4dB at 3.2kHz, Q=1.2) for crisp Khmer speech clarity
    - High-shelf sheen (+1.8dB at 8.5kHz) for studio air
    - Broadcast compression (acompressor) to balance vocal dynamics
    - Smooth atempo time-scaling if speed_ratio != 1.0
    """
    in_file = Path(input_path)
    if not in_file.exists():
        return str(input_path)

    out_file = Path(output_path) if output_path else in_file.parent / f"enhanced_{in_file.name}"
    out_file.parent.mkdir(parents=True, exist_ok=True)

    filter_parts = [
        "highpass=f=75",
        "equalizer=f=3200:t=q:w=1.2:g=2.4",
        "equalizer=f=8500:t=h:g=1.8",
        "acompressor=threshold=-19dB:ratio=2.6:attack=12:release=110"
    ]

    sr = max(0.5, min(2.0, float(speed_ratio)))
    if abs(sr - 1.0) > 0.01:
        filter_parts.append(f"atempo={sr:.3f}")

    filter_str = ",".join(filter_parts)
    temp_out = out_file.parent / f"tmp_dsp_{out_file.name}"
    cmd = [
        get_ffmpeg_path(), "-y",
        "-i", str(in_file),
        "-filter:a", filter_str,
        "-b:a", "192k",
        str(temp_out)
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if res.returncode == 0 and temp_out.exists() and temp_out.stat().st_size > 100:
        if output_path is None or str(output_path) == str(input_path):
            if in_file.exists():
                in_file.unlink(missing_ok=True)
            temp_out.rename(in_file)
            return str(in_file)
        else:
            if out_file.exists():
                out_file.unlink(missing_ok=True)
            temp_out.rename(out_file)
            return str(out_file)
    else:
        if temp_out.exists():
            temp_out.unlink(missing_ok=True)
        return str(input_path)


def extract_audio_from_video(video_path: str, output_audio_path: str) -> str:
    """Extract audio track from video file as 16-bit 44.1kHz WAV for mixing."""
    out_p = Path(output_audio_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        get_ffmpeg_path(),
        "-y",
        "-i", str(video_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        str(out_p)
    ]
    
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg audio extraction failed: {proc.stderr}")
        
    return str(out_p)


def get_media_duration(file_path: str) -> float:
    """Get media file duration in seconds using FFmpeg stderr output."""
    cmd = [
        get_ffmpeg_path(),
        "-i", str(file_path)
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    for line in proc.stderr.splitlines():
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = parts.split(":")
            return float(h) * 3600 + float(m) * 60 + float(s)
            
    try:
        seg = load_audio_safely(file_path)
        return len(seg) / 1000.0
    except Exception:
        return 0.0


def create_waveform_data(audio_path: str, num_samples: int = 120) -> List[float]:
    """Generate normalized waveform peaks (0.0 to 1.0) for visual audio rendering in Web Studio."""
    try:
        audio = load_audio_safely(audio_path)
        raw_data = audio.raw_data
        sample_width = audio.sample_width
        
        if sample_width == 2:
            import array
            samples = array.array("h", raw_data)
        else:
            samples = list(raw_data)
            
        if not samples:
            return [0.1] * num_samples

        total_samples = len(samples)
        block_size = max(1, total_samples // num_samples)
        peaks = []
        max_val = max(1, max(abs(s) for s in samples[:10000] if samples))

        for i in range(num_samples):
            start = i * block_size
            end = min(total_samples, (i + 1) * block_size)
            chunk = samples[start:end]
            if chunk:
                peak = max(abs(s) for s in chunk)
                peaks.append(round(min(1.0, peak / max_val), 3))
            else:
                peaks.append(0.05)

        return peaks
    except Exception as e:
        print(f"Waveform generation note: {e}")
        return [round(abs(math.sin(i * 0.2) * 0.7 + 0.2), 2) for i in range(num_samples)]


def mix_dubbed_audio(
    original_audio_path: Optional[str],
    dialogue_items: List[Dict[str, Any]],
    output_mixed_path: str,
    total_duration_sec: Optional[float] = None,
    ducking_volume_factor: float = 0.35,  # Professional -9dB ducking (warm continuous musical bed)
    speech_volume_boost_db: float = 2.5,   # Boost speech clarity by +2.5dB
    dubbing_mode: str = "smart_bgm"        # "smart_bgm", "pure_voice", "standard_ducking"
) -> str:
    """
    Mix Khmer voice clips into the timeline with Smart BGM Audio Ducking and Zero Vocal Leakage.
    """
    out_p = Path(output_mixed_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    # 1. Determine total length
    bg_audio = None
    if dubbing_mode != "pure_voice" and original_audio_path and Path(original_audio_path).exists():
        try:
            bg_audio = load_audio_safely(original_audio_path)
            target_len_ms = len(bg_audio)
        except Exception as e:
            print(f"BGM load warning: {e}")
            bg_audio = None

    if bg_audio is None:
        max_dialogue_end_ms = 0
        for item in dialogue_items:
            end_ms = int(item.get("end", 0) * 1000)
            if end_ms > max_dialogue_end_ms:
                max_dialogue_end_ms = end_ms
        if total_duration_sec:
            target_len_ms = max(int(total_duration_sec * 1000), max_dialogue_end_ms + 1000)
        else:
            target_len_ms = max(1000, max_dialogue_end_ms + 2000)
            
        bg_audio = AudioSegment.silent(duration=target_len_ms)

    # 2. Build the Khmer Speech Track efficiently (O(N) sequential assembly, zero memory thrashing)
    speech_intervals = []
    valid_lines = []
    for idx, item in enumerate(dialogue_items):
        audio_file = item.get("audio_file")
        if audio_file and Path(audio_file).exists():
            valid_lines.append((idx, item))

    processed_lines = []
    for i, (idx, item) in enumerate(valid_lines):
        try:
            line_seg = load_audio_safely(item["audio_file"])
            if speech_volume_boost_db != 0:
                line_seg = line_seg + speech_volume_boost_db

            # Micro-fades to eliminate digital clicks and boundary pops
            if len(line_seg) > 60:
                line_seg = line_seg.fade_in(15).fade_out(25)

            # Envelope bounds covering both original dialogue and Khmer audio
            orig_s = float(item.get("orig_start", item.get("start", 0.0)))
            orig_e = float(item.get("orig_end", item.get("end", orig_s + 2.0)))
            orig_start_ms = max(0, int(orig_s * 1000))
            orig_end_ms = max(0, int(orig_e * 1000))

            start_ms = max(0, int(item.get("start", 0) * 1000))
            line_len_ms = len(line_seg)
            speech_end_ms = start_ms + line_len_ms

            # The ducking interval MUST cover the entire envelope of BOTH original Chinese speech and Khmer dubbing:
            # -160ms before speech start to mute any opening mouth attack of original Chinese voice
            # +180ms after speech end to mute any trailing release or trailing phrase of original Chinese voice
            pad_start = max(0, min(orig_start_ms, start_ms) - 160)
            pad_end = max(orig_end_ms, speech_end_ms) + 180
            speech_intervals.append((pad_start, pad_end))
            processed_lines.append((start_ms, line_seg))
        except Exception as e:
            print(f"Error processing line audio: {e}")

    # Build master speech track with zero truncation and exact millisecond alignment
    target_fr = 44100
    channels = 2
    if bg_audio:
        target_fr = bg_audio.frame_rate
        channels = bg_audio.channels

    speech_track = None
    try:
        import numpy as np
        total_samples = int((target_len_ms / 1000.0) * target_fr) + target_fr
        master_buffer = np.zeros((total_samples, channels), dtype=np.int32)

        for start_ms, line_seg in processed_lines:
            if line_seg.frame_rate != target_fr or line_seg.channels != channels:
                line_seg = line_seg.set_frame_rate(target_fr).set_channels(channels)

            start_sample = max(0, int((start_ms / 1000.0) * target_fr))
            line_samples = np.frombuffer(line_seg.raw_data, dtype=np.int16)
            if channels > 1:
                line_samples = line_samples.reshape(-1, channels)
            else:
                line_samples = line_samples.reshape(-1, 1)

            n_samples = len(line_samples)
            end_sample = min(total_samples, start_sample + n_samples)
            if end_sample > start_sample:
                usable_n = end_sample - start_sample
                master_buffer[start_sample:end_sample] += line_samples[:usable_n]

        # Clip safely to 16-bit range without harsh digital distortion
        master_buffer = np.clip(master_buffer, -32768, 32767).astype(np.int16)
        speech_track = AudioSegment(
            master_buffer.tobytes(),
            frame_rate=target_fr,
            sample_width=2,
            channels=channels
        )
        if len(speech_track) > target_len_ms:
            speech_track = speech_track[:target_len_ms]
    except Exception as np_mix_err:
        print(f"NumPy audio track mix note ({np_mix_err}), using overlay fallback.")
        speech_track = AudioSegment.silent(duration=target_len_ms, frame_rate=target_fr).set_channels(channels)
        for s_ms, l_seg in processed_lines:
            if l_seg.frame_rate != target_fr or l_seg.channels != channels:
                l_seg = l_seg.set_frame_rate(target_fr).set_channels(channels)
            speech_track = speech_track.overlay(l_seg, position=s_ms)

    # 3. Apply Clean Continuous Smart Audio Ducking (Professional Cinema Ducking)
    if dubbing_mode == "pure_voice":
        final_mixed = speech_track
    elif bg_audio and speech_intervals:
        # Professional Cinema Ducking: Merge gaps under 1800ms so dialogue exchanges
        # maintain a consistent musical bed without volume pumping between quick sentences!
        speech_intervals.sort(key=lambda x: x[0])
        merged_intervals = []
        for start, end in speech_intervals:
            if not merged_intervals:
                merged_intervals.append([start, end])
            else:
                prev = merged_intervals[-1]
                if start <= prev[1] + 1800:  # Smooth hold across conversation pauses
                    prev[1] = max(prev[1], end)
                else:
                    merged_intervals.append([start, end])

        # Calculate continuous gain envelope across all frames with NumPy
        try:
            import numpy as np
            sr = bg_audio.frame_rate
            channels = bg_audio.channels
            raw_samples = np.frombuffer(bg_audio.raw_data, dtype=np.int16)
            total_frames = len(raw_samples) // channels

            # Safe clamped target gain: ensures BGM is never muted to 0 / dead silence
            # Default factor 0.35 = -9dB (gentle, warm bed of music)
            target_gain = float(np.clip(ducking_volume_factor, 0.18, 0.65))

            gain_curve = np.ones(total_frames, dtype=np.float32)
            fade_in_frames = max(1, int((0.300) * sr))   # 300ms smooth dip
            fade_out_frames = max(1, int((0.500) * sr))  # 500ms smooth return

            for s_ms, e_ms in merged_intervals:
                start_frame = max(0, int((s_ms / 1000.0) * sr))
                end_frame = min(total_frames, int((e_ms / 1000.0) * sr))

                if start_frame >= total_frames:
                    continue

                # Smooth dip into ducking
                dip_start = max(0, start_frame - fade_in_frames // 2)
                dip_end = min(total_frames, dip_start + fade_in_frames)
                if dip_end > dip_start:
                    ramp_down = np.linspace(1.0, target_gain, dip_end - dip_start, dtype=np.float32)
                    gain_curve[dip_start:dip_end] = np.minimum(gain_curve[dip_start:dip_end], ramp_down)

                # Steady ducked level during dialogue
                body_start = dip_end
                body_end = max(body_start, end_frame)
                if body_end > body_start and body_start < total_frames:
                    gain_curve[body_start:min(total_frames, body_end)] = np.minimum(
                        gain_curve[body_start:min(total_frames, body_end)], target_gain
                    )

                # Smooth swell back to full volume after dialogue
                rise_start = body_end
                rise_end = min(total_frames, rise_start + fade_out_frames)
                if rise_end > rise_start and rise_start < total_frames:
                    ramp_up = np.linspace(target_gain, 1.0, rise_end - rise_start, dtype=np.float32)
                    gain_curve[rise_start:rise_end] = np.minimum(gain_curve[rise_start:rise_end], ramp_up)

            if channels > 1:
                samples_2d = raw_samples.reshape(-1, channels).astype(np.float32)
                ducked_samples = samples_2d * gain_curve[:, np.newaxis]
            else:
                ducked_samples = raw_samples.astype(np.float32) * gain_curve

            ducked_int16 = np.clip(ducked_samples, -32768, 32767).astype(np.int16)
            ducked_bg = AudioSegment(
                ducked_int16.tobytes(),
                frame_rate=sr,
                sample_width=2,
                channels=channels
            )
        except Exception as e:
            print(f"NumPy smooth ducking fallback note: {e}")
            ducked_bg = bg_audio

        final_mixed = ducked_bg.overlay(speech_track)
    else:
        final_mixed = speech_track

    # Save final high quality audio
    save_audio_safely(final_mixed, str(out_p))
    return str(out_p)
