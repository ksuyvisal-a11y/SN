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

    # FFmpeg Stereo Center-Channel Vocal Suppression + Multi-Band Vocal Frequency Notch
    # Human voice core frequencies: 250Hz - 3600Hz.
    # We suppress center-channel speech and apply targeted notches across vocal bands:
    bgm_filter = (
        "stereotools=mlev=0.02:slev=1.35:mpan=0.0:sbal=0.0,"
        "equalizer=f=320:t=q:w=1.5:g=-16,"
        "equalizer=f=1000:t=q:w=1.8:g=-20,"
        "equalizer=f=2200:t=q:w=1.8:g=-18,"
        "equalizer=f=3300:t=q:w=1.5:g=-14"
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
    if proc_bgm.returncode != 0:
        # Fallback to direct copy if filter fails
        shutil.copy(str(in_p), str(bgm_output))

    # Vocal isolation filter: Extract center channel dialogue and suppress stereo BGM
    # In movies, dialogues are panned center (L+R in-phase), while stereo BGM & SFX are on the sides.
    # stereotools with slev=0.0 eliminates stereo sides while preserving dialogue at 16kHz mono.
    vocal_filter = (
        "stereotools=mlev=1.6:slev=0.0:mpan=0.0,"
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
            "-ac", "1",
            str(vocals_output)
        ]
        subprocess.run(cmd_fallback, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return str(bgm_output), str(vocals_output)
