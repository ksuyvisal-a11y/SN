import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from audio_processor import get_ffmpeg_path

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

    # FFmpeg Stereo Center-Channel Vocal Cancellation (L - R)
    # Both channels are kept strictly IN-PHASE so there is ZERO phase cancellation on mobile phone speakers or social media.
    bgm_filter = (
        "pan=stereo|c0=0.5*c0-0.5*c1|c1=0.5*c0-0.5*c1,"
        "equalizer=f=280:t=q:w=1.5:g=-6,"
        "equalizer=f=1000:t=q:w=2.0:g=-10,"
        "equalizer=f=2200:t=q:w=2.0:g=-10,"
        "equalizer=f=3200:t=q:w=1.8:g=-6"
    )

    cmd_bgm = [
        get_ffmpeg_path(),
        "-y",
        "-i", str(in_p),
        "-af", bgm_filter,
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        str(bgm_output)
    ]

    proc_bgm = subprocess.run(cmd_bgm, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc_bgm.returncode != 0 or not bgm_output.exists() or bgm_output.stat().st_size < 1000:
        # Robust Mono/Stereo Fallback: Multiband speech notch filtering
        fallback_filter = (
            "equalizer=f=300:t=q:w=1.5:g=-18,"
            "equalizer=f=1000:t=q:w=2.0:g=-24,"
            "equalizer=f=2200:t=q:w=2.0:g=-24,"
            "equalizer=f=3200:t=q:w=1.8:g=-20"
        )
        cmd_bgm_fallback = [
            get_ffmpeg_path(),
            "-y",
            "-i", str(in_p),
            "-af", fallback_filter,
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            str(bgm_output)
        ]
        subprocess.run(cmd_bgm_fallback, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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
    proc_voc = subprocess.run(cmd_voc, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
        subprocess.run(cmd_fallback, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return str(bgm_output), str(vocals_output)
