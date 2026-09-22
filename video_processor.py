"""
Video Processing Engine: Video Rendering, Audio Replacement, Subtitle Burning, Aspect Ratio (9:16/16:9), and Watermarking
"""
import os
import re
import time
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from audio_processor import get_ffmpeg_path
from translator import format_srt_content
from subtitle_styler import generate_ass_subtitles


def get_video_dimensions(video_path: str):
    """Extract width and height of video quickly via FFmpeg."""
    try:
        cmd = [get_ffmpeg_path(), "-i", str(video_path)]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore")
        m = re.search(r'Stream.*Video:.*?(\d{3,5})x(\d{3,5})', res.stderr)
        if m:
            return int(m.group(1)), int(m.group(2))
    except Exception:
        pass
    return None, None



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
    burn_subtitles: bool = False,
    aspect_ratio: str = "16:9",  # "16:9" or "9:16"
    watermark_text: Optional[str] = None,
    temp_dir: str = "cache/temp"
) -> str:
    """
    Render final dubbed video with new audio, subtitle burning, vertical 9:16 aspect ratio framing, and watermark.
    Ultra-fast execution with boxblur (replaces slow gblur) and robust filter chaining.
    """
    out_p = Path(output_video_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    t_dir = Path(temp_dir)
    t_dir.mkdir(parents=True, exist_ok=True)

    # 1. Prepare ASS/SRT Subtitles
    ass_path = None
    if burn_subtitles and dialogues:
        ass_content = generate_ass_subtitles(dialogues)
        ass_file = t_dir / "subtitles_khmer.ass"
        with open(ass_file, "w", encoding="utf-8") as f:
            f.write(ass_content)
        ass_path = str(ass_file).replace("\\", "/").replace(":", "\\:")

    # 2. Detect video orientation
    w, h = get_video_dimensions(original_video_path)
    is_already_vertical = (w is not None and h is not None and w < h)

    # 3. Construct FFmpeg command
    cmd = [
        get_ffmpeg_path(),
        "-y",
        "-i", str(original_video_path),
        "-i", str(mixed_audio_path)
    ]

    simple_filters = []
    if ass_path:
        simple_filters.append(f"ass='{ass_path}'")
    if watermark_text and watermark_text.strip():
        wm_clean = watermark_text.replace("'", "").replace(":", "")
        simple_filters.append(f"drawtext=text='{wm_clean}':fontsize=24:fontcolor=white@0.8:x=30:y=30:box=1:boxcolor=black@0.4:boxborderw=6")

    # If 9:16 requested but input video is landscape (w >= h), frame it with blurred background
    if aspect_ratio == "9:16" and not is_already_vertical:
        filter_complex = (
            "[0:v]split[bg][fg];"
            "[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=12:1[bg_blur];"
            "[fg]scale=1080:-1[fg_scaled];"
            "[bg_blur][fg_scaled]overlay=(W-w)/2:(H-h)/2"
        )
        current_pad = "[v_padded]"
        filter_complex += current_pad

        if simple_filters:
            filter_complex += f";{current_pad}{','.join(simple_filters)}[v_out]"
            v_map = "[v_out]"
        else:
            v_map = "[v_padded]"

        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", v_map,
            "-map", "1:a:0",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(out_p)
        ])
    else:
        # 16:9, original aspect ratio, or already vertical video
        if simple_filters:
            cmd.extend([
                "-vf", ",".join(simple_filters),
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "22",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                str(out_p)
            ])
        else:
            cmd.extend([
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "22",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                str(out_p)
            ])

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        print(f"Render fallback triggered: {proc.stderr[:200]}")
        # Direct mux fallback with universal H.264
        fallback_cmd = [
            get_ffmpeg_path(),
            "-y",
            "-i", str(original_video_path),
            "-i", str(mixed_audio_path),
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            str(out_p)
        ]
        subprocess.run(fallback_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Always ensure a copy exists in data/exports for easy user access!
    try:
        import shutil
        exports_dir = Path("data/exports")
        exports_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(original_video_path).stem
        export_copy = exports_dir / f"Dubbed_{stem}.mp4"
        shutil.copy2(str(out_p), str(export_copy))
    except Exception as e:
        print(f"Export copy note: {e}")

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

