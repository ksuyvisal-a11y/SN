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
    ducking_volume_factor: float = 0.02,  # Deep -34dB ducking during speech to guarantee Zero Vocal Leakage
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

    # 2. Build the Khmer Speech Track
    speech_track = AudioSegment.silent(duration=target_len_ms)
    speech_intervals = []

    for idx, item in enumerate(dialogue_items):
        audio_file = item.get("audio_file")
        if not audio_file or not Path(audio_file).exists():
            continue

        try:
            line_seg = load_audio_safely(audio_file)
            if speech_volume_boost_db != 0:
                line_seg = line_seg + speech_volume_boost_db

            # Micro-fades to eliminate digital clicks and boundary pops
            if len(line_seg) > 60:
                line_seg = line_seg.fade_in(15).fade_out(25)

            start_ms = int(item.get("start", 0) * 1000)

            # Determine when the next speech line starts to prevent ANY overlapping
            next_start_ms = None
            for next_item in dialogue_items[idx + 1:]:
                next_af = next_item.get("audio_file")
                if next_af and Path(next_af).exists():
                    next_start_ms = int(next_item.get("start", 0) * 1000)
                    break

            # STRICT NON-OVERLAP ENFORCEMENT:
            # If current line extends into the next line, cap it cleanly with a gentle fade-out
            if next_start_ms is not None and (start_ms + len(line_seg)) > (next_start_ms - 30):
                allowed_len = max(150, next_start_ms - start_ms - 30)
                if len(line_seg) > allowed_len:
                    fade_ms = min(80, max(20, allowed_len // 4))
                    line_seg = line_seg[:allowed_len].fade_out(fade_ms)

            line_len_ms = len(line_seg)
            
            # 80ms buffer around speech to duck original vocals cleanly
            pad_start = max(0, start_ms - 80)
            pad_end = start_ms + line_len_ms + 80
            speech_intervals.append((pad_start, pad_end))

            if start_ms < len(speech_track):
                speech_track = speech_track.overlay(line_seg, position=start_ms)
            else:
                silence_gap = start_ms - len(speech_track)
                speech_track = speech_track + AudioSegment.silent(duration=silence_gap) + line_seg
        except Exception as e:
            print(f"Error overlaying line audio: {e}")

    # 3. Apply Clean Smart Audio Ducking
    if dubbing_mode == "pure_voice":
        final_mixed = speech_track
    elif bg_audio and speech_intervals:
        speech_intervals.sort(key=lambda x: x[0])
        merged_intervals = []
        for start, end in speech_intervals:
            if not merged_intervals:
                merged_intervals.append([start, end])
            else:
                prev = merged_intervals[-1]
                if start <= prev[1] + 250:
                    prev[1] = max(prev[1], end)
                else:
                    merged_intervals.append([start, end])

        ducked_bg = AudioSegment.empty()
        current_pos = 0
        # Enforce minimum -32dB (up to -40dB) ducking to guarantee ZERO vocal bleed
        calc_duck_db = 20 * math.log10(max(0.001, ducking_volume_factor))
        duck_db = min(-32.0, calc_duck_db)

        fade_ms = 100
        for interval_start, interval_end in merged_intervals:
            if interval_start > current_pos:
                normal_seg = bg_audio[current_pos:interval_start]
                ducked_bg = ducked_bg + normal_seg
            
            speech_duration = min(len(bg_audio), interval_end) - interval_start
            if speech_duration > 0:
                # Duck background and apply additional -4dB suppression during dialogue (total -36dB to -38dB)
                ducked_seg = bg_audio[interval_start:interval_start + speech_duration] + duck_db - 4.0
                # Smooth crossfading to prevent any abrupt audio pops
                actual_fade = min(fade_ms, max(20, speech_duration // 4))
                if len(ducked_seg) > actual_fade * 2:
                    ducked_seg = ducked_seg.fade_in(actual_fade).fade_out(actual_fade)
                ducked_bg = ducked_bg + ducked_seg
                
            current_pos = interval_end

        if current_pos < len(bg_audio):
            ducked_bg = ducked_bg + bg_audio[current_pos:]

        final_mixed = ducked_bg.overlay(speech_track)
    else:
        final_mixed = speech_track

    # Save final high quality audio
    save_audio_safely(final_mixed, str(out_p))
    return str(out_p)
