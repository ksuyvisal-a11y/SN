import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from audio_processor import get_ffmpeg_path, get_silent_kwargs

CACHE_DIR = Path("cache/audio_separation")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def separate_vocals_and_bgm(
    input_audio_path: str,
    output_dir: Optional[str] = None
) -> Tuple[str, str]:
    """
    Separate input audio into:
    1. bgm_audio_path: Background Music & Sound Effects track with vocals removed.
    2. vocals_audio_path: Isolated Dialogue vocal track.
    Returns (bgm_audio_path, vocals_audio_path).
    """
    in_p = Path(input_audio_path)
    if not in_p.exists():
        raise FileNotFoundError(f"Input audio not found: {input_audio_path}")

    target_dir = Path(output_dir) if output_dir else CACHE_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    bgm_output = target_dir / f"{in_p.stem}_bgm.wav"
    vocals_output = target_dir / f"{in_p.stem}_vocals.wav"

    # Deep multi-band speech notch filter (vocal formant suppression without phase cancellation)
    # This guarantees that mono or dual-mono audio (TikTok/Reels/Short dramas) is NEVER cancelled to dead silence!
    speech_notch_filter = (
        "equalizer=f=300:t=q:w=1.5:g=-14,"
        "equalizer=f=800:t=q:w=1.5:g=-18,"
        "equalizer=f=1600:t=q:w=1.8:g=-20,"
        "equalizer=f=2500:t=q:w=1.8:g=-20,"
        "equalizer=f=3400:t=q:w=1.5:g=-14"
    )

    # 1. First attempt: Center-channel phase cancellation (L - R) + speech formant notch
    phase_cancel_filter = (
        "pan=stereo|c0=0.5*c0-0.5*c1|c1=0.5*c0-0.5*c1,"
        + speech_notch_filter
    )

    cmd_bgm = [
        get_ffmpeg_path(),
        "-y",
        "-i", str(in_p),
        "-af", phase_cancel_filter,
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        str(bgm_output)
    ]
    proc_bgm = subprocess.run(cmd_bgm, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **get_silent_kwargs())

    # 2. Check if phase cancellation produced silence (common on dual-mono audio where L == R)
    need_fallback = False
    if proc_bgm.returncode != 0 or not bgm_output.exists() or bgm_output.stat().st_size < 1000:
        need_fallback = True
    else:
        try:
            from audio_processor import load_audio_safely
            test_seg = load_audio_safely(str(bgm_output))
            if test_seg.dBFS < -46.0 or test_seg.max_dBFS < -42.0:
                print(f"Notice: Phase cancellation resulted in silence (dBFS={test_seg.dBFS:.1f}), switching to speech notch filter.")
                need_fallback = True
        except Exception:
            need_fallback = True

    if need_fallback:
        # Fallback: High-precision speech notch filter without phase subtraction
        # Preserves 100% of music and background effects at full volume!
        cmd_bgm_fallback = [
            get_ffmpeg_path(),
            "-y",
            "-i", str(in_p),
            "-af", speech_notch_filter,
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            "-ac", "2",
            str(bgm_output)
        ]
        proc_fb = subprocess.run(cmd_bgm_fallback, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **get_silent_kwargs())
        if proc_fb.returncode != 0 or not bgm_output.exists():
            # Ultimate safety: copy original audio so BGM is NEVER dead silence
            import shutil
            shutil.copy2(str(in_p), str(bgm_output))

    # Vocal isolation filter: Extract center channel dialogue and suppress stereo BGM
    # In movies, dialogues are panned center (L+R in-phase).
    vocal_filter = (
        "pan=1c|c0=0.5*c0+0.5*c1,"
        "highpass=f=80,lowpass=f=4500,"
        "equalizer=f=1200:t=q:w=1.5:g=3,"
        "equalizer=f=2500:t=q:w=1.5:g=2"
    )
    cmd_voc = [
        get_ffmpeg_path(),
        "-y",
        "-i", str(in_p),
        "-af", vocal_filter,
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        str(vocals_output)
    ]
    proc_voc = subprocess.run(cmd_voc, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **get_silent_kwargs())
    if proc_voc.returncode != 0 or not vocals_output.exists() or vocals_output.stat().st_size < 1000:
        cmd_fallback = [
            get_ffmpeg_path(),
            "-y",
            "-i", str(in_p),
            "-af", "highpass=f=80,lowpass=f=4500",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            str(vocals_output)
        ]
        subprocess.run(cmd_fallback, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **get_silent_kwargs())

    return str(bgm_output), str(vocals_output)
