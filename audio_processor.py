"""
Audio Processor Engine: Audio Extraction, Time Alignment, Waveform Generation, and Smart BGM Audio Ducking
"""
import os
import io
import math
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
import pydub
from pydub import AudioSegment

try:
    import imageio_ffmpeg
    FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
    FFMPEG_DIR = os.path.dirname(FFMPEG_EXE)
    if FFMPEG_DIR not in os.environ.get("PATH", ""):
        os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")
except Exception:
    FFMPEG_EXE = "ffmpeg"


def get_ffmpeg_path() -> str:
    """Get reliable ffmpeg binary path."""
    return FFMPEG_EXE


def load_audio_safely(file_path: str) -> AudioSegment:
    """
    Robust audio loader that decodes MP3/AAC/WAV/etc directly via FFmpeg binary.
    Does not require ffprobe.
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
    
    # Export segment to in-memory WAV buffer
    wav_io = io.BytesIO()
    segment.export(wav_io, format="wav")
    wav_io.seek(0)
    
    # Encode with FFmpeg
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
    ducking_volume_factor: float = 0.25,  # Reduce original BGM to 25% during speech
    speech_volume_boost_db: float = 2.0,  # Boost speech by +2dB
    fade_duration_ms: int = 200
) -> str:
    """
    Mix Khmer voice clips into the timeline with Smart Audio Ducking for original BGM.
    - original_audio_path: path to original video audio (or None for voice-only recap)
    - dialogue_items: list of items with 'start', 'end', and 'audio_file'
    - output_mixed_path: destination path for mixed audio
    """
    out_p = Path(output_mixed_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    # 1. Determine total length
    if original_audio_path and Path(original_audio_path).exists():
        try:
            bg_audio = load_audio_safely(original_audio_path)
            target_len_ms = len(bg_audio)
        except Exception:
            bg_audio = None
            target_len_ms = 1000
    else:
        bg_audio = None
        target_len_ms = 1000

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

    # 2. Build the Speech Track
    speech_track = AudioSegment.silent(duration=target_len_ms)
    speech_intervals = []

    for item in dialogue_items:
        audio_file = item.get("audio_file")
        if not audio_file or not Path(audio_file).exists():
            continue

        try:
            line_seg = load_audio_safely(audio_file)
            if speech_volume_boost_db != 0:
                line_seg = line_seg + speech_volume_boost_db

            start_ms = int(item.get("start", 0) * 1000)
            line_len_ms = len(line_seg)
            
            speech_intervals.append((start_ms, start_ms + line_len_ms))

            if start_ms < len(speech_track):
                speech_track = speech_track.overlay(line_seg, position=start_ms)
            else:
                silence_gap = start_ms - len(speech_track)
                speech_track = speech_track + AudioSegment.silent(duration=silence_gap) + line_seg
        except Exception as e:
            print(f"Error overlaying line audio: {e}")

    # 3. Apply Audio Ducking to Original Background Audio
    if original_audio_path and Path(original_audio_path).exists() and speech_intervals and bg_audio:
        speech_intervals.sort(key=lambda x: x[0])
        merged_intervals = []
        for start, end in speech_intervals:
            if not merged_intervals:
                merged_intervals.append([start, end])
            else:
                prev = merged_intervals[-1]
                if start <= prev[1] + 300:
                    prev[1] = max(prev[1], end)
                else:
                    merged_intervals.append([start, end])

        ducked_bg = AudioSegment.empty()
        current_pos = 0
        duck_db = 20 * math.log10(max(0.01, ducking_volume_factor))

        for interval_start, interval_end in merged_intervals:
            if interval_start > current_pos:
                normal_seg = bg_audio[current_pos:interval_start]
                ducked_bg = ducked_bg + normal_seg
            
            speech_duration = min(len(bg_audio), interval_end) - interval_start
            if speech_duration > 0:
                ducked_seg = bg_audio[interval_start:interval_start + speech_duration] + duck_db
                ducked_bg = ducked_bg + ducked_seg
                
            current_pos = interval_end

        if current_pos < len(bg_audio):
            ducked_bg = ducked_bg + bg_audio[current_pos:]

        final_mixed = ducked_bg.overlay(speech_track)
    else:
        final_mixed = speech_track

    # Save safely
    save_audio_safely(final_mixed, str(out_p))
    return str(out_p)
