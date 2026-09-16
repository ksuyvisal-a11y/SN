"""
Video Processing Engine: Video Rendering, Audio Replacement, Subtitle Burning, Aspect Ratio (9:16/16:9), and Watermarking
"""
import os
import time
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from audio_processor import get_ffmpeg_path
from translator import format_srt_content
from subtitle_styler import generate_ass_subtitles


def generate_sample_drama_video(output_video_path: str, duration_sec: int = 15) -> str:
    """Generate sample drama MP4 video for quick testing."""
    out_p = Path(output_video_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        get_ffmpeg_path(),
        "-y",
        "-f", "lavfi",
        "-i", f"testsrc=duration={duration_sec}:size=1280x720:rate=30",
        "-f", "lavfi",
        "-i", f"sine=frequency=440:duration={duration_sec}",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        str(out_p)
    ]

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Failed to generate sample drama video: {proc.stderr}")

    return str(out_p)


def render_dubbed_video(
    original_video_path: str,
    mixed_audio_path: str,
    output_video_path: str,
    dialogues: Optional[List[Dict[str, Any]]] = None,
    burn_subtitles: bool = True,
    aspect_ratio: str = "16:9",  # "16:9" or "9:16"
    watermark_text: Optional[str] = None,
    temp_dir: str = "cache/temp"
) -> str:
    """
    Render final dubbed video with new audio, subtitle burning, vertical 9:16 aspect ratio framing, and watermark.
    """
    out_p = Path(output_video_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    t_dir = Path(temp_dir)
    t_dir.mkdir(parents=True, exist_ok=True)

    # 1. Prepare ASS/SRT Subtitles
    sub_filter_part = None
    if burn_subtitles and dialogues:
        ass_content = generate_ass_subtitles(dialogues)
        ass_path = t_dir / "subtitles_khmer.ass"
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(ass_content)
        
        ass_escaped = str(ass_path).replace("\\", "/").replace(":", "\\:")
        sub_filter_part = f"ass='{ass_escaped}'"

    # 2. Build Video Filter Graph
    video_filters = []

    # Aspect Ratio 9:16 Vertical Framing (Reels / TikTok style with blurred background)
    if aspect_ratio == "9:16":
        # Split into background (blurred and scaled to 1080x1920) and foreground (scaled with original aspect)
        video_filters.append("split[bg][fg];[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=25[bg_blur];[fg]scale=1080:-1[fg_scaled];[bg_blur][fg_scaled]overlay=(W-w)/2:(H-h)/2")
    
    # Subtitles
    if sub_filter_part:
        video_filters.append(sub_filter_part)

    # Watermark text overlay
    if watermark_text and watermark_text.strip():
        wm_clean = watermark_text.replace("'", "").replace(":", "")
        video_filters.append(f"drawtext=text='{wm_clean}':fontsize=24:fontcolor=white@0.8:x=30:y=30:box=1:boxcolor=black@0.4:boxborderw=6")

    # Combine filters or use stream copy
    cmd = [
        get_ffmpeg_path(),
        "-y",
        "-i", str(original_video_path),
        "-i", str(mixed_audio_path)
    ]

    if video_filters:
        vf_str = ",".join(video_filters)
        cmd.extend([
            "-vf", vf_str,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-pix_fmt", "yuv420p"
        ])
    else:
        cmd.extend([
            "-c:v", "copy"
        ])

    cmd.extend([
        "-c:a", "aac",
        "-b:a", "192k",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        str(out_p)
    ])

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        print(f"Render fallback triggered: {proc.stderr[:200]}")
        # Direct mux fallback
        fallback_cmd = [
            get_ffmpeg_path(),
            "-y",
            "-i", str(original_video_path),
            "-i", str(mixed_audio_path),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            str(out_p)
        ]
        subprocess.run(fallback_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return str(out_p)


def merge_videos(video_paths: List[str], output_path: str) -> str:
    """Merge multiple video clips / drama episodes into a single MP4 file."""
    if not video_paths:
        raise ValueError("No video paths provided for merging.")
    
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    # Create concat list file
    list_file = out_p.parent / f"concat_list_{int(time.time())}.txt"
    try:
        with open(list_file, "w", encoding="utf-8") as f:
            for vp in video_paths:
                p_abs = Path(vp).resolve()
                f.write(f"file '{str(p_abs).replace(chr(92), '/')}'\n")

        cmd = [
            get_ffmpeg_path(),
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(out_p)
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            # Re-encoding concat fallback
            inputs = []
            filter_parts = []
            for idx, vp in enumerate(video_paths):
                inputs.extend(["-i", str(vp)])
                filter_parts.append(f"[{idx}:v:0][{idx}:a:0]")
            
            filter_complex = f"{''.join(filter_parts)}concat=n={len(video_paths)}:v=1:a=1[v][a]"
            cmd_reencode = [
                get_ffmpeg_path(),
                "-y",
                *inputs,
                "-filter_complex", filter_complex,
                "-map", "[v]",
                "-map", "[a]",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "aac",
                str(out_p)
            ]
            subprocess.run(cmd_reencode, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    finally:
        if list_file.exists():
            try:
                list_file.unlink()
            except Exception:
                pass

    return str(out_p)


def split_video(video_path: str, chunk_duration_sec: int, output_dir: str) -> List[str]:
    """Split a video into segments of chunk_duration_sec."""
    in_p = Path(video_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_pattern = str(out_dir / f"{in_p.stem}_part%03d.mp4")
    cmd = [
        get_ffmpeg_path(),
        "-y",
        "-i", str(in_p),
        "-c", "copy",
        "-map", "0",
        "-segment_time", str(chunk_duration_sec),
        "-f", "segment",
        "-reset_timestamps", "1",
        out_pattern
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return [str(p) for p in sorted(out_dir.glob(f"{in_p.stem}_part*.mp4"))]


def batch_rename_files(file_paths: List[str], prefix: str = "Drama_EP", start_num: int = 1) -> List[Dict[str, str]]:
    """Batch rename video files to a standardized format."""
    results = []
    for idx, fp in enumerate(file_paths, start=start_num):
        p = Path(fp)
        new_name = f"{prefix}{idx:02d}{p.suffix}"
        new_path = p.parent / new_name
        try:
            if p.exists() and p != new_path:
                p.rename(new_path)
            results.append({"old": str(p), "new": str(new_path), "name": new_name})
        except Exception as e:
            results.append({"old": str(p), "new": str(p), "error": str(e)})
    return results


def compress_video(video_path: str, output_path: str, crf: int = 26, preset: str = "fast", target_height: Optional[int] = None) -> str:
    """Compress video using H.264 with optimized CRF and optional downscaling."""
    in_p = Path(video_path)
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        get_ffmpeg_path(),
        "-y",
        "-i", str(in_p)
    ]
    
    if target_height:
        cmd.extend(["-vf", f"scale=-2:{target_height}"])
        
    cmd.extend([
        "-c:v", "libx264",
        "-crf", str(crf),
        "-preset", preset,
        "-c:a", "aac",
        "-b:a", "128k",
        str(out_p)
    ])
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return str(out_p)

