"""
Video Processing Engine: Video Rendering, Audio Replacement, Subtitle Burning, Aspect Ratio (9:16/16:9), and Watermarking
"""
import os
import re
import time
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from audio_processor import get_ffmpeg_path, get_silent_kwargs
from translator import format_srt_content
from subtitle_styler import generate_ass_subtitles


def get_video_dimensions(video_path: str):
    """Extract width and height of video quickly via FFmpeg."""
    try:
        cmd = [get_ffmpeg_path(), "-nostdin", "-i", str(video_path)]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore", timeout=10, **get_silent_kwargs())
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

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", **get_silent_kwargs())
    if proc.returncode != 0:
        raise RuntimeError(f"Failed to generate sample drama video: {proc.stderr or ''}")

    return str(out_p)


def render_dubbed_video(
    original_video_path: str,
    mixed_audio_path: str,
    output_video_path: str,
    dialogues: Optional[List[Dict[str, Any]]] = None,
    burn_subtitles: bool = False,
    aspect_ratio: str = "16:9",  # "16:9" or "9:16"
    watermark_text: Optional[str] = None,
    overlay_config: Optional[Dict[str, Any]] = None,
    temp_dir: str = "cache/temp"
) -> str:
    """
    Render final dubbed video with new audio, subtitle burning, vertical 9:16 aspect ratio framing, 
    interactive Logo watermark overlay, and interactive Blur mask box.
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

    # 2. Parse Logo and Blur Configurations
    logo_cfg = overlay_config.get("logo") if isinstance(overlay_config, dict) else None
    blur_cfg = overlay_config.get("blur") if isinstance(overlay_config, dict) else None

    logo_active = bool(logo_cfg and logo_cfg.get("active") and logo_cfg.get("path") and Path(str(logo_cfg.get("path"))).exists())
    logo_path = str(logo_cfg.get("path")) if logo_active else None

    blur_active = bool(blur_cfg and blur_cfg.get("active"))

    # 3. Detect video orientation & dimensions
    w, h = get_video_dimensions(original_video_path)
    w = w or 1920
    h = h or 1080
    is_already_vertical = (w < h)

    # 4. Phase 1 Turbo Optimization: Lossless Stream Copy Mode (1-2 seconds per episode!)
    # Only if NO subtitles, NO watermark, NO logo, NO blur, and no 9:16 framing needed
    can_use_stream_copy = (not ass_path) and (not watermark_text) and (not logo_active) and (not blur_active) and (is_already_vertical or aspect_ratio != "9:16")
    if can_use_stream_copy:
        fast_cmd = [
            get_ffmpeg_path(),
            "-nostdin",
            "-y",
            "-i", str(original_video_path),
            "-i", str(mixed_audio_path),
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "48000",
            "-ac", "2",
            "-shortest",
            str(out_p)
        ]
        fast_proc = subprocess.run(fast_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60, **get_silent_kwargs())
        if fast_proc.returncode == 0 and out_p.exists() and out_p.stat().st_size > 5000:
            try:
                import shutil
                exports_dir = Path("data/exports")
                exports_dir.mkdir(parents=True, exist_ok=True)
                stem = Path(original_video_path).stem
                export_copy = exports_dir / f"Dubbed_{stem}.mp4"
                shutil.copy2(str(out_p), str(export_copy))
            except Exception:
                pass
            return str(out_p)

    # 5. Build FFmpeg command inputs
    cmd = [
        get_ffmpeg_path(),
        "-nostdin",
        "-y",
        "-i", str(original_video_path),
        "-i", str(mixed_audio_path)
    ]

    logo_input_idx = None
    if logo_active and logo_path:
        cmd.extend(["-i", str(logo_path)])
        logo_input_idx = 2

    # 6. Determine target dimensions & base video layout
    filter_parts = []
    if aspect_ratio == "9:16" and not is_already_vertical:
        target_w = 1080
        target_h = 1920
        filter_parts.append(
            "[0:v]split[bg][fg];"
            "[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=12:1[bg_blur];"
            "[fg]scale=1080:-2[fg_scaled];"
            "[bg_blur][fg_scaled]overlay=(W-w)/2:(H-h)/2[v_base]"
        )
        current_v = "[v_base]"
    else:
        target_w = (w // 2) * 2
        target_h = (h // 2) * 2
        filter_parts.append(f"[0:v]scale={target_w}:{target_h}[v_base]")
        current_v = "[v_base]"

    # 7. Apply Blur Mask Box Filter
    if blur_active:
        norm_x = float(blur_cfg.get("norm_x", 0.75))
        norm_y = float(blur_cfg.get("norm_y", 0.03))
        norm_w = float(blur_cfg.get("norm_w", 0.20))
        norm_h = float(blur_cfg.get("norm_h", 0.08))
        radius = max(5, min(50, int(blur_cfg.get("radius", 25))))

        bw = max(16, min(target_w, int(target_w * norm_w)))
        bh = max(16, min(target_h, int(target_h * norm_h)))
        bx = max(0, min(target_w - bw, int(target_w * norm_x)))
        by = max(0, min(target_h - bh, int(target_h * norm_y)))

        bx = (bx // 2) * 2
        by = (by // 2) * 2
        bw = (bw // 2) * 2
        bh = (bh // 2) * 2

        b_power = min(radius, 25)
        filter_parts.append(
            f"{current_v}split[v_pre_blur][v_crop_in];"
            f"[v_crop_in]crop=w={bw}:h={bh}:x={bx}:y={by},boxblur={b_power}:2[v_blurred_box];"
            f"[v_pre_blur][v_blurred_box]overlay=x={bx}:y={by}[v_after_blur]"
        )
        current_v = "[v_after_blur]"

    # 8. Apply Logo Watermark Overlay Filter
    if logo_active and logo_path and logo_input_idx is not None:
        logo_norm_x = float(logo_cfg.get("norm_x", 0.82))
        logo_norm_y = float(logo_cfg.get("norm_y", 0.04))
        logo_norm_w = float(logo_cfg.get("norm_w", 0.14))
        opacity = max(0.1, min(1.0, float(logo_cfg.get("opacity", 1.0))))

        lw = max(32, min(target_w, int(target_w * logo_norm_w)))
        lw = (lw // 2) * 2
        lx = max(0, min(target_w - lw, int(target_w * logo_norm_x)))
        ly = max(0, min(target_h - 32, int(target_h * logo_norm_y)))

        filter_parts.append(
            f"[{logo_input_idx}:v]scale={lw}:-1,format=rgba,colorchannelmixer=aa={opacity:.2f}[logo_scaled];"
            f"{current_v}[logo_scaled]overlay=x={lx}:y={ly}[v_after_logo]"
        )
        current_v = "[v_after_logo]"

    # 9. Apply ASS Subtitles Burning
    if ass_path:
        filter_parts.append(f"{current_v}ass='{ass_path}'[v_after_subs]")
        current_v = "[v_after_subs]"

    # 10. Apply Watermark Text
    if watermark_text and watermark_text.strip():
        wm_clean = watermark_text.replace("'", "").replace(":", "")
        filter_parts.append(
            f"{current_v}drawtext=text='{wm_clean}':fontsize=24:fontcolor=white@0.8:x=30:y=30:box=1:boxcolor=black@0.4:boxborderw=6[v_after_wm]"
        )
        current_v = "[v_after_wm]"

    # 11. Final Filter Complex and Encoding Flags
    full_filter_complex = ";".join(filter_parts)
    cmd.extend([
        "-filter_complex", full_filter_complex,
        "-map", current_v,
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "48000",
        "-ac", "2",
        "-shortest",
        str(out_p)
    ])

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", timeout=7200, **get_silent_kwargs())
    if proc.returncode != 0:
        err_prev = (proc.stderr or '')[:200]
        print(f"Render fallback triggered: {err_prev}")
        # Direct mux fallback with universal H.264 and even dimension scaling
        fallback_cmd = [
            get_ffmpeg_path(),
            "-nostdin",
            "-y",
            "-i", str(original_video_path),
            "-i", str(mixed_audio_path),
            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "48000",
            "-ac", "2",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            str(out_p)
        ]
        subprocess.run(fallback_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=7200, **get_silent_kwargs())

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
            "-nostdin",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(out_p)
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", timeout=7200, **get_silent_kwargs())
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
                "-nostdin",
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
            subprocess.run(cmd_reencode, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=7200, **get_silent_kwargs())
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
        "-nostdin",
        "-y",
        "-i", str(in_p),
        "-c", "copy",
        "-map", "0",
        "-segment_time", str(chunk_duration_sec),
        "-f", "segment",
        "-reset_timestamps", "1",
        out_pattern
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600, **get_silent_kwargs())
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
        "-nostdin",
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
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600, **get_silent_kwargs())
    return str(out_p)

