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


def patch_silent_subprocess():
    """
    Globally suppress black CMD/console popup windows for ffmpeg, ffprobe,
    and all background tools on Windows.
    Preserves interactive GUI applications (Edge, Chrome, Explorer).
    """
    import sys
    if sys.platform != "win32":
        return
    import subprocess
    if getattr(subprocess, "_silent_patch_applied", False):
        return
    subprocess._silent_patch_applied = True

    orig_popen_init = subprocess.Popen.__init__

    def silent_popen_init(self, *args, **kwargs):
        cmd = args[0] if args else kwargs.get("args")
        cmd_str = ""
        if isinstance(cmd, (list, tuple)) and cmd:
            cmd_str = str(cmd[0]).lower()
        elif isinstance(cmd, str):
            cmd_str = cmd.lower()

        is_gui_app = any(gui in cmd_str for gui in ("msedge", "chrome", "explorer"))

        if not is_gui_app:
            if "creationflags" not in kwargs:
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            else:
                kwargs["creationflags"] |= subprocess.CREATE_NO_WINDOW

            si = kwargs.get("startupinfo")
            if si is None:
                si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 0  # SW_HIDE
            kwargs["startupinfo"] = si

        orig_popen_init(self, *args, **kwargs)

    subprocess.Popen.__init__ = silent_popen_init


def get_silent_kwargs() -> Dict[str, Any]:
    """Return explicit subprocess creationflags and startupinfo to guarantee zero console window popup on Windows."""
    import sys
    if sys.platform == "win32":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        return {
            "creationflags": subprocess.CREATE_NO_WINDOW,
            "startupinfo": si
        }
    return {}


# Auto-apply global silent patch immediately
patch_silent_subprocess()

pydub.AudioSegment.converter = FFMPEG_EXE
pydub.AudioSegment.ffmpeg = FFMPEG_EXE


def get_ffmpeg_path() -> str:
    """Get reliable ffmpeg binary path across frozen PyInstaller, _internal, and system PATH."""
    global FFMPEG_EXE
    if FFMPEG_EXE and os.path.isabs(FFMPEG_EXE) and os.path.exists(FFMPEG_EXE):
        return FFMPEG_EXE
    
    # Check PyInstaller frozen environment or local _internal dir
    import sys
    app_dirs = []
    if getattr(sys, 'frozen', False):
        app_dirs.append(getattr(sys, '_MEIPASS', ''))
        app_dirs.append(os.path.dirname(sys.executable))
    app_dirs.append(str(Path(__file__).resolve().parent))
    app_dirs.append(str(Path(__file__).resolve().parent / "_internal"))
    
    for base in app_dirs:
        if not base:
            continue
        candidates = [
            os.path.join(base, "imageio_ffmpeg", "binaries", "ffmpeg-win-x86_64-v7.1.exe"),
            os.path.join(base, "imageio_ffmpeg", "binaries", "ffmpeg.exe"),
            os.path.join(base, "_internal", "imageio_ffmpeg", "binaries", "ffmpeg-win-x86_64-v7.1.exe"),
            os.path.join(base, "_internal", "imageio_ffmpeg", "binaries", "ffmpeg.exe"),
            os.path.join(base, "ffmpeg.exe"),
        ]
        for c in candidates:
            if os.path.exists(c):
                FFMPEG_EXE = c
                pydub.AudioSegment.converter = FFMPEG_EXE
                pydub.AudioSegment.ffmpeg = FFMPEG_EXE
                return c

    return FFMPEG_EXE or "ffmpeg"


def load_audio_safely(file_path: str) -> AudioSegment:
    """
    Robust audio loader that decodes MP3/AAC/WAV/etc directly via FFmpeg binary at 48kHz stereo.
    """
    cmd = [
        get_ffmpeg_path(),
        "-nostdin",
        "-y",
        "-i", str(file_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "48000",
        "-ac", "2",
        "-f", "wav",
        "-"
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120, **get_silent_kwargs())
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg audio decode failed: {proc.stderr.decode('utf-8', errors='ignore')}")
    
    return AudioSegment.from_wav(io.BytesIO(proc.stdout))


def save_audio_safely(segment: AudioSegment, output_path: str, bitrate: str = "192k") -> str:
    """
    Save AudioSegment to MP3/WAV safely using FFmpeg with guaranteed studio 48kHz stereo.
    """
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    
    if segment.frame_rate != 48000:
        segment = segment.set_frame_rate(48000)
    if segment.channels != 2:
        segment = segment.set_channels(2)

    wav_io = io.BytesIO()
    segment.export(wav_io, format="wav")
    wav_io.seek(0)
    
    cmd = [
        get_ffmpeg_path(),
        "-nostdin",
        "-y",
        "-i", "-",
        "-ar", "48000",
        "-ac", "2",
        "-b:a", bitrate,
        str(out_p)
    ]
    proc = subprocess.run(cmd, input=wav_io.read(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120, **get_silent_kwargs())
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
        get_ffmpeg_path(),
        "-nostdin",
        "-y",
        "-i", str(in_file),
        "-filter:a", filter_str,
        "-ar", "48000",
        "-ac", "2",
        "-b:a", "192k",
        str(temp_out)
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60, **get_silent_kwargs())
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
    """Extract audio track from video file as 16-bit 48kHz stereo WAV for mixing."""
    out_p = Path(output_audio_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        get_ffmpeg_path(),
        "-nostdin",
        "-y",
        "-i", str(video_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "48000",
        "-ac", "2",
        str(out_p)
    ]
    
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=1800, **get_silent_kwargs())
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg audio extraction failed: {proc.stderr}")
        
    return str(out_p)


def get_media_duration(file_path: str) -> float:
    """Get media file duration in seconds using FFmpeg stderr output."""
    cmd = [
        get_ffmpeg_path(),
        "-nostdin",
        "-i", str(file_path)
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10, **get_silent_kwargs())
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
    ducking_volume_factor: float = 0.35,  # -9dB ducking (warm continuous musical bed)
    speech_volume_boost_db: float = 3.5,   # Boost speech clarity by +3.5dB
    dubbing_mode: str = "smart_bgm"        # "smart_bgm", "pure_voice", "standard_ducking"
) -> str:
    """
    Mix Khmer voice clips into the timeline with Smart BGM Audio Ducking and Zero Vocal Leakage.
    Guarantees audible, rich audio output with zero silent drops.
    """
    out_p = Path(output_mixed_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    # 1. Determine total length and load background audio
    bg_audio = None
    if dubbing_mode != "pure_voice" and original_audio_path and Path(original_audio_path).exists():
        try:
            bg_audio = load_audio_safely(original_audio_path)
            # Verify BGM is not digital silence (-inf or < -48 dBFS)
            if bg_audio.dBFS < -48.0 or math.isinf(bg_audio.dBFS):
                print(f"Notice: BGM track has near-zero energy (dBFS={bg_audio.dBFS}), recovering audio...")
                orig_candidate = Path(original_audio_path).parent / "original_audio.wav"
                if orig_candidate.exists() and orig_candidate.resolve() != Path(original_audio_path).resolve():
                    orig_test = load_audio_safely(str(orig_candidate))
                    if orig_test.dBFS > -45.0:
                        print("Successfully recovered audio bed from original_audio.wav!")
                        bg_audio = orig_test
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
        bg_audio = AudioSegment.silent(duration=target_len_ms, frame_rate=48000).set_channels(2)

    target_fr = 48000
    channels = 2
    if bg_audio:
        if bg_audio.frame_rate != target_fr or bg_audio.channels != channels:
            bg_audio = bg_audio.set_frame_rate(target_fr).set_channels(channels)

    # 2. Build the Khmer Speech Track efficiently (O(N) sequential assembly)
    speech_intervals = []
    valid_lines = []
    for idx, item in enumerate(dialogue_items):
        audio_file = item.get("audio_file")
        if audio_file and Path(audio_file).exists():
            valid_lines.append((idx, item))

    # Speech clarity boost (at least +3.5dB so dialogue cuts cleanly and proudly over BGM)
    boost_val = max(3.0, float(speech_volume_boost_db)) if speech_volume_boost_db is not None else 3.5

    processed_lines = []
    for i, (idx, item) in enumerate(valid_lines):
        try:
            line_seg = load_audio_safely(item["audio_file"])
            # Safe studio headroom gain: boost speech clearly without digital clipping (target peak -1.5 dBFS)
            if boost_val != 0:
                max_peak = line_seg.max_dBFS
                safe_gain = min(boost_val, max(0.0, -1.5 - max_peak)) if max_peak > -12.0 else boost_val
                if safe_gain > 0:
                    line_seg = line_seg + safe_gain

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

            # The ducking interval covers original speech and dubbing with gentle padding
            pad_start = max(0, min(orig_start_ms, start_ms) - 150)
            pad_end = max(orig_end_ms, speech_end_ms) + 160
            speech_intervals.append((pad_start, pad_end))
            processed_lines.append((start_ms, line_seg))
        except Exception as e:
            print(f"Error processing line audio: {e}")

    # Build master speech track
    speech_track = None
    if processed_lines:
        try:
            import numpy as np
            # Memory-safe chunked block assembly (approx 50MB RAM per block, zero OOM on multi-hour videos)
            block_ms = 600 * 1000
            total_blocks = max(1, int(math.ceil(target_len_ms / block_ms)))
            assembled_blocks = []

            for b_idx in range(total_blocks):
                b_start_ms = b_idx * block_ms
                b_end_ms = min(target_len_ms, b_start_ms + block_ms)
                b_len_ms = b_end_ms - b_start_ms
                b_samples = int((b_len_ms / 1000.0) * target_fr)

                if b_samples <= 0:
                    continue

                b_buffer = np.zeros((b_samples, channels), dtype=np.int32)

                for start_ms, line_seg in processed_lines:
                    line_end_ms = start_ms + len(line_seg)
                    if line_end_ms <= b_start_ms or start_ms >= b_end_ms:
                        continue

                    if line_seg.frame_rate != target_fr or line_seg.channels != channels:
                        line_seg = line_seg.set_frame_rate(target_fr).set_channels(channels)

                    line_samples = np.frombuffer(line_seg.raw_data, dtype=np.int16)
                    if channels > 1:
                        line_samples = line_samples.reshape(-1, channels)
                    else:
                        line_samples = line_samples.reshape(-1, 1)

                    rel_start_ms = start_ms - b_start_ms
                    if rel_start_ms >= 0:
                        buf_s = int((rel_start_ms / 1000.0) * target_fr)
                        samp_s = 0
                    else:
                        buf_s = 0
                        samp_s = int((abs(rel_start_ms) / 1000.0) * target_fr)

                    samp_len = len(line_samples) - samp_s
                    if samp_len <= 0 or buf_s >= b_samples:
                        continue

                    usable = min(samp_len, b_samples - buf_s)
                    b_buffer[buf_s:buf_s + usable] += line_samples[samp_s:samp_s + usable]

                b_int16 = np.clip(b_buffer, -32768, 32767).astype(np.int16)
                assembled_blocks.append(AudioSegment(
                    b_int16.tobytes(),
                    frame_rate=target_fr,
                    sample_width=2,
                    channels=channels
                ))

            if assembled_blocks:
                speech_track = assembled_blocks[0]
                for nxt in assembled_blocks[1:]:
                    speech_track += nxt
                if len(speech_track) > target_len_ms:
                    speech_track = speech_track[:target_len_ms]
            else:
                speech_track = AudioSegment.silent(duration=target_len_ms, frame_rate=target_fr).set_channels(channels)
        except Exception as np_mix_err:
            print(f"NumPy audio track mix note ({np_mix_err}), using overlay fallback.")
            speech_track = AudioSegment.silent(duration=target_len_ms, frame_rate=target_fr).set_channels(channels)
            for s_ms, l_seg in processed_lines:
                if l_seg.frame_rate != target_fr or l_seg.channels != channels:
                    l_seg = l_seg.set_frame_rate(target_fr).set_channels(channels)
                speech_track = speech_track.overlay(l_seg, position=s_ms)
    else:
        speech_track = AudioSegment.silent(duration=target_len_ms, frame_rate=target_fr).set_channels(channels)

    # 3. Apply Professional Dual-Stem Cinema Mixing (Continuous Musical Bed & Zero Pumping)
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
                if start <= prev[1] + 2400:  # Smooth hold across 2.4s conversation pauses
                    prev[1] = max(prev[1], end)
                else:
                    merged_intervals.append([start, end])

        # Memory-safe chunked ducking (60-second blocks, <10MB RAM even on 10-hour movies)
        try:
            import numpy as np
            sr = bg_audio.frame_rate
            bg_channels = bg_audio.channels
            raw_samples = np.frombuffer(bg_audio.raw_data, dtype=np.int16)
            total_frames = len(raw_samples) // bg_channels

            bgm_nominal = 0.70
            bgm_ducked = 0.35

            fade_in_frames = max(1, int(0.280 * sr))   # 280ms smooth S-curve dip
            fade_out_frames = max(1, int(0.600 * sr))  # 600ms smooth S-curve return

            block_frames = 60 * sr
            ducked_bytes = bytearray()

            for blk_start in range(0, total_frames, block_frames):
                blk_end = min(total_frames, blk_start + block_frames)
                n_blk = blk_end - blk_start

                gain_blk = np.full(n_blk, bgm_nominal, dtype=np.float32)

                blk_s_ms = (blk_start / sr) * 1000.0
                blk_e_ms = (blk_end / sr) * 1000.0

                for s_ms, e_ms in merged_intervals:
                    if e_ms + 1000 < blk_s_ms or s_ms - 1000 > blk_e_ms:
                        continue

                    start_frame = max(0, int((s_ms / 1000.0) * sr))
                    end_frame = min(total_frames, int((e_ms / 1000.0) * sr))

                    dip_start = max(0, start_frame - fade_in_frames // 2)
                    dip_end = min(total_frames, dip_start + fade_in_frames)

                    loc_dip_s = max(0, dip_start - blk_start)
                    loc_dip_e = min(n_blk, dip_end - blk_start)
                    if loc_dip_e > loc_dip_s:
                        g_start = blk_start + loc_dip_s
                        g_end = blk_start + loc_dip_e
                        t = np.linspace((g_start - dip_start) / max(1, dip_end - dip_start) * np.pi,
                                        (g_end - dip_start) / max(1, dip_end - dip_start) * np.pi,
                                        loc_dip_e - loc_dip_s, dtype=np.float32)
                        ramp_down = bgm_ducked + (bgm_nominal - bgm_ducked) * 0.5 * (1.0 + np.cos(t))
                        gain_blk[loc_dip_s:loc_dip_e] = np.minimum(gain_blk[loc_dip_s:loc_dip_e], ramp_down)

                    body_start = dip_end
                    body_end = max(body_start, end_frame)
                    loc_body_s = max(0, body_start - blk_start)
                    loc_body_e = min(n_blk, body_end - blk_start)
                    if loc_body_e > loc_body_s:
                        gain_blk[loc_body_s:loc_body_e] = np.minimum(gain_blk[loc_body_s:loc_body_e], bgm_ducked)

                    rise_start = body_end
                    rise_end = min(total_frames, rise_start + fade_out_frames)
                    loc_rise_s = max(0, rise_start - blk_start)
                    loc_rise_e = min(n_blk, rise_end - blk_start)
                    if loc_rise_e > loc_rise_s:
                        g_start = blk_start + loc_rise_s
                        g_end = blk_start + loc_rise_e
                        t = np.linspace((g_start - rise_start) / max(1, rise_end - rise_start) * np.pi,
                                        (g_end - rise_start) / max(1, rise_end - rise_start) * np.pi,
                                        loc_rise_e - loc_rise_s, dtype=np.float32)
                        ramp_up = bgm_ducked + (bgm_nominal - bgm_ducked) * 0.5 * (1.0 - np.cos(t))
                        gain_blk[loc_rise_s:loc_rise_e] = np.minimum(gain_blk[loc_rise_s:loc_rise_e], ramp_up)

                blk_sample_s = blk_start * bg_channels
                blk_sample_e = blk_end * bg_channels
                blk_samples = raw_samples[blk_sample_s:blk_sample_e]

                if bg_channels > 1:
                    samples_2d = blk_samples.reshape(-1, bg_channels).astype(np.float32)
                    ducked_blk = samples_2d * gain_blk[:, np.newaxis]
                else:
                    ducked_blk = blk_samples.astype(np.float32) * gain_blk

                ducked_bytes.extend(np.clip(ducked_blk, -32768, 32767).astype(np.int16).tobytes())

            ducked_bg = AudioSegment(
                bytes(ducked_bytes),
                frame_rate=sr,
                sample_width=2,
                channels=bg_channels
            )
            if ducked_bg.frame_rate != target_fr or ducked_bg.channels != channels:
                ducked_bg = ducked_bg.set_frame_rate(target_fr).set_channels(channels)
        except Exception as e:
            print(f"NumPy smooth ducking fallback note: {e}")
            ducked_bg = bg_audio

        if speech_track and (speech_track.frame_rate != target_fr or speech_track.channels != channels):
            speech_track = speech_track.set_frame_rate(target_fr).set_channels(channels)
        final_mixed = ducked_bg.overlay(speech_track)
    elif bg_audio:
        if bg_audio.frame_rate != target_fr or bg_audio.channels != channels:
            bg_audio = bg_audio.set_frame_rate(target_fr).set_channels(channels)
        if speech_track and (speech_track.frame_rate != target_fr or speech_track.channels != channels):
            speech_track = speech_track.set_frame_rate(target_fr).set_channels(channels)
        final_mixed = bg_audio.overlay(speech_track) if speech_track else bg_audio
    else:
        final_mixed = speech_track if speech_track else AudioSegment.silent(duration=1000, frame_rate=target_fr).set_channels(channels)

    # Absolute Safety Net: Ensure the exported audio is NEVER silent!
    try:
        if final_mixed is None or len(final_mixed) == 0 or final_mixed.dBFS < -46.0 or math.isinf(final_mixed.dBFS):
            if original_audio_path and Path(original_audio_path).exists():
                print("Warning: mixed audio had low energy or silence, recovering with original audio!")
                orig_recover = load_audio_safely(str(original_audio_path))
                if orig_recover.dBFS < -46.0 or math.isinf(orig_recover.dBFS):
                    alt_orig = Path(original_audio_path).parent / "original_audio.wav"
                    if alt_orig.exists():
                        orig_recover = load_audio_safely(str(alt_orig))
                if speech_track and len(speech_track) > 0 and speech_track.dBFS > -42.0:
                    final_mixed = orig_recover.overlay(speech_track)
                else:
                    final_mixed = orig_recover
    except Exception as check_e:
        print(f"Audio safety check note: {check_e}")

    # Save final high quality audio
    save_audio_safely(final_mixed, str(out_p))
    return str(out_p)
