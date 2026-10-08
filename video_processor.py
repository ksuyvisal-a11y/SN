"""
Video Processing Engine: Video Rendering, Audio Replacement, Subtitle Burning, Aspect Ratio (9:16/16:9), and Watermarking
"""
import os
import re
import time
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
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


def format_ass_filter_path(file_path: Union[str, Path]) -> str:
    """Format an ASS file path for safe insertion into FFmpeg filter_complex on Windows and POSIX."""
    p = Path(file_path).resolve()
    try:
        rel = p.relative_to(Path.cwd().resolve()).as_posix()
        return f"ass='{rel}'"
    except Exception:
        esc = p.as_posix().replace(":", r"\:")
        return f"ass={esc}"


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
    ass_filter_cmd = None
    if burn_subtitles and dialogues:
        ass_content = generate_ass_subtitles(dialogues)
        ass_file = t_dir / "subtitles_khmer.ass"
        with open(ass_file, "w", encoding="utf-8") as f:
            f.write(ass_content)
        ass_filter_cmd = format_ass_filter_path(ass_file)

    # 2. Parse Logo, Blur, Text, and Lower Third Configurations
    logo_cfg = overlay_config.get("logo") if isinstance(overlay_config, dict) else None
    blur_cfg = overlay_config.get("blur") if isinstance(overlay_config, dict) else None
    text_cfg = overlay_config.get("text") if isinstance(overlay_config, dict) else None
    lower_third_cfg = overlay_config.get("lower_third") if isinstance(overlay_config, dict) else None

    logo_active = bool(logo_cfg and logo_cfg.get("active") and logo_cfg.get("path") and Path(str(logo_cfg.get("path"))).exists())
    logo_path = str(Path(str(logo_cfg.get("path"))).resolve()) if logo_active else None

    blur_active = bool(blur_cfg and blur_cfg.get("active"))
    text_active = bool(text_cfg and text_cfg.get("active") and text_cfg.get("text"))

    lt_active = bool(lower_third_cfg and lower_third_cfg.get("active") and lower_third_cfg.get("path") and Path(str(lower_third_cfg.get("path"))).exists())
    lt_path = str(Path(str(lower_third_cfg.get("path"))).resolve()) if lt_active else None

    # 3. Detect video orientation & dimensions
    w, h = get_video_dimensions(original_video_path)
    w = w or 1920
    h = h or 1080
    is_already_vertical = (w < h)

    # 4. Phase 1 Turbo Optimization: Lossless Stream Copy Mode (1-2 seconds per episode!)
    # Only if NO subtitles, NO watermark, NO logo, NO blur, NO text, NO lower third, and no 9:16 framing needed
    can_use_stream_copy = (not ass_filter_cmd) and (not watermark_text) and (not logo_active) and (not blur_active) and (not text_active) and (not lt_active) and (is_already_vertical or aspect_ratio != "9:16")
    if can_use_stream_copy:
        fast_cmd = [
            get_ffmpeg_path(),
            "-nostdin",
            "-y",
            "-fflags", "+genpts",
            "-avoid_negative_ts", "make_zero",
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

    current_input_idx = 2
    logo_input_idx = None
    if logo_active and logo_path:
        cmd.extend(["-i", str(logo_path)])
        logo_input_idx = current_input_idx
        current_input_idx += 1

    lt_input_idx = None
    if lt_active and lt_path:
        lt_loop = bool(lower_third_cfg.get("loop", True))
        if lt_loop:
            cmd.extend(["-stream_loop", "-1"])
        cmd.extend(["-i", str(lt_path)])
        lt_input_idx = current_input_idx
        current_input_idx += 1

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
        norm_x = float(blur_cfg.get("norm_x", 0.0))
        norm_y = float(blur_cfg.get("norm_y", 0.50))
        norm_w = float(blur_cfg.get("norm_w", 1.0))
        norm_h = float(blur_cfg.get("norm_h", 0.08))
        radius = max(5, min(50, int(blur_cfg.get("radius", 25))))

        bw = max(16, min(target_w, int(target_w * norm_w)))
        bh = max(16, min(target_h, int(target_h * norm_h)))
        bx = max(0, min(target_w - bw, int(target_w * norm_x)))
        by = max(0, min(target_h - bh, int(target_h * norm_y)))

        # Snap to exact horizontal center if user centered it or selected centered preset
        is_blur_center = bool(blur_cfg.get("is_center")) or (norm_w >= 0.85) or (abs((bx + bw / 2.0) - target_w / 2.0) < (target_w * 0.04))
        if is_blur_center:
            if norm_w >= 0.88:
                bx = 0
                bw = target_w
            else:
                bx = max(0, (target_w - bw) // 2)

        bx = (bx // 2) * 2
        by = (by // 2) * 2
        bw = (bw // 2) * 2
        bh = (bh // 2) * 2

        bh = max(32, bh)
        b_power = max(2, min(radius, (bw // 4) - 1, (bh // 4) - 1, 18))
        filter_parts.append(
            f"{current_v}split[v_pre_blur][v_crop_in];"
            f"[v_crop_in]crop=w={bw}:h={bh}:x={bx}:y={by},boxblur={b_power}:2[v_blurred_box];"
            f"[v_pre_blur][v_blurred_box]overlay=x={bx}:y={by}[v_after_blur]"
        )
        current_v = "[v_after_blur]"

    # 8. Apply Logo Watermark Overlay Filter
    if logo_active and logo_path and logo_input_idx is not None:
        logo_norm_x = float(logo_cfg.get("norm_x", 0.04))
        logo_norm_y = float(logo_cfg.get("norm_y", 0.04))
        logo_norm_w = float(logo_cfg.get("norm_w", 0.16))
        opacity = max(0.1, min(1.0, float(logo_cfg.get("opacity", 1.0))))

        lw = max(32, min(target_w, int(target_w * logo_norm_w)))
        lw = (lw // 2) * 2
        lx = max(0, min(target_w - lw, int(target_w * logo_norm_x)))
        ly = max(0, min(target_h - 32, int(target_h * logo_norm_y)))

        is_logo_center = bool(logo_cfg.get("is_center")) or (abs((lx + lw / 2.0) - target_w / 2.0) < (target_w * 0.04))
        if is_logo_center:
            lx = max(0, (target_w - lw) // 2)

        filter_parts.append(
            f"[{logo_input_idx}:v]scale={lw}:-1,format=rgba,colorchannelmixer=aa={opacity:.2f}[logo_scaled];"
            f"{current_v}[logo_scaled]overlay=x={lx}:y={ly}[v_after_logo]"
        )
        current_v = "[v_after_logo]"

    # 8.5 Apply Lower Third Video Overlay
    if lt_active and lt_path and lt_input_idx is not None:
        lt_norm_x = float(lower_third_cfg.get("norm_x", 0.05))
        lt_norm_y = float(lower_third_cfg.get("norm_y", 0.80))
        lt_norm_w = float(lower_third_cfg.get("norm_w", 0.65))
        lt_opacity = max(0.05, min(1.0, float(lower_third_cfg.get("opacity", 1.0))))
        lt_speed = max(0.25, min(4.0, float(lower_third_cfg.get("speed", 1.0))))
        lt_start = max(0.0, float(lower_third_cfg.get("start_time", 0.0)))
        lt_end = float(lower_third_cfg.get("end_time", 0.0))

        lt_w = max(48, min(target_w, int(target_w * lt_norm_w)))
        lt_w = (lt_w // 2) * 2
        lt_x = max(0, min(target_w - lt_w, int(target_w * lt_norm_x)))
        lt_y = max(0, min(target_h - 48, int(target_h * lt_norm_y)))

        is_lt_center = bool(lower_third_cfg.get("is_center")) or (abs((lt_x + lt_w / 2.0) - target_w / 2.0) < (target_w * 0.04))
        if is_lt_center:
            lt_x = max(0, (target_w - lt_w) // 2)

        # Build enable condition
        if lt_end > lt_start and lt_end > 0.05:
            enable_expr = f":enable='between(t,{lt_start:.2f},{lt_end:.2f})'"
        elif lt_start > 0.05:
            enable_expr = f":enable='gte(t,{lt_start:.2f})'"
        else:
            enable_expr = ""

        # Build speed filter (pts multiplier = 1 / speed)
        speed_factor = 1.0 / lt_speed
        pts_filter = f"setpts={speed_factor:.3f}*PTS,"

        filter_parts.append(
            f"[{lt_input_idx}:v]{pts_filter}scale={lt_w}:-2,format=rgba,colorchannelmixer=aa={lt_opacity:.2f}[lt_scaled];"
            f"{current_v}[lt_scaled]overlay=x={lt_x}:y={lt_y}{enable_expr}[v_after_lt]"
        )
        current_v = "[v_after_lt]"

    # 9. Apply ASS Subtitles Burning
    if ass_filter_cmd:
        filter_parts.append(f"{current_v}{ass_filter_cmd}[v_after_subs]")
        current_v = "[v_after_subs]"

    # 10. Apply Watermark Text
    if watermark_text and watermark_text.strip():
        wm_clean = watermark_text.replace("'", "").replace(":", "")
        filter_parts.append(
            f"{current_v}drawtext=text='{wm_clean}':fontsize=24:fontcolor=white@0.8:x=30:y=30:box=1:boxcolor=black@0.4:boxborderw=6[v_after_wm]"
        )
        current_v = "[v_after_wm]"

    # 10.5 Apply Watermark/Title Text Overlay (Universal High-Fidelity ASS Engine)
    if text_active:
        t_raw = str(text_cfg.get("text", "")).strip()
        if t_raw:
            t_size = int(text_cfg.get("size", 24))
            norm_fs = float(text_cfg.get("norm_font_size", 0.0))
            if norm_fs > 0.005:
                ass_fontsize = max(24, int(round(target_h * norm_fs)))
            else:
                ass_fontsize = max(28, int(round(t_size * (target_h / 560.0))))

            t_center_x = float(text_cfg.get("center_x", text_cfg.get("norm_center_x", 0.50)))
            t_norm_y = float(text_cfg.get("norm_y", 0.85))
            is_center = bool(text_cfg.get("is_center")) or (abs(t_center_x - 0.50) < 0.04)
            if is_center:
                t_center_x = 0.50

            t_color = str(text_cfg.get("color", "#ffffff")).lstrip("#")
            t_bg = bool(text_cfg.get("bg", True))
            t_motion = str(text_cfg.get("motion", "static")).lower()
            t_speed = max(15, min(250, int(text_cfg.get("speed", 65))))
            segments = text_cfg.get("segments") or []

            t_col_hex = t_color.strip().lstrip('#')
            if len(t_col_hex) == 6:
                tr, tg, tb = t_col_hex[0:2], t_col_hex[2:4], t_col_hex[4:6]
            else:
                tr, tg, tb = "FF", "FF", "FF"
            style_primary = f"&H00{tb}{tg}{tr}&"

            def _hex_to_ass_inline(h_str: str) -> str:
                h = h_str.strip().lstrip('#')
                if len(h) != 6:
                    return "&HFFFFFF&"
                r, g, b = h[0:2], h[2:4], h[4:6]
                return f"&H{b}{g}{r}&"

            ass_styled_text = ""
            if isinstance(segments, list) and len(segments) > 0:
                for seg in segments:
                    if not isinstance(seg, dict):
                        continue
                    w_txt = str(seg.get("text", "")).replace("{", "").replace("}", "")
                    w_col = str(seg.get("color", "#" + t_color))
                    ass_styled_text += f"{{\\c{_hex_to_ass_inline(w_col)}}}{w_txt} "
                ass_styled_text = ass_styled_text.strip()
            else:
                clean_t = t_raw.replace("{", "").replace("}", "")
                ass_styled_text = clean_t

            ass_file = t_dir / "title_overlay.ass"
            border_style = 3 if t_bg else 1
            back_color = "&HA0000000" if t_bg else "&H80000000"
            outline_w = max(4, int(ass_fontsize * 0.12)) if t_bg else max(3, int(ass_fontsize * 0.08))
            shadow_val = 0 if t_bg else 1.5

            pos_x = int(target_w * t_center_x)
            pos_y = int(target_h * t_norm_y)

            ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {target_w}
PlayResY: {target_h}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TitleStyle,Kantumruy Pro,{ass_fontsize},{style_primary},&H000000FF,&H00000000,{back_color},-1,0,0,0,100,100,0,0,{border_style},{outline_w},{shadow_val},8,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
            ass_events = []
            if t_motion == "scroll_up":
                cycle_duration = max(3.0, (target_h + 100.0) / float(t_speed))
                total_cycles = int(7200 / cycle_duration) + 1
                for c_idx in range(min(total_cycles, 600)):
                    c_start = c_idx * cycle_duration
                    c_end = (c_idx + 1) * cycle_duration
                    s_str = f"{int(c_start//3600)}:{int((c_start%3600)//60):02d}:{c_start%60:05.2f}"
                    e_str = f"{int(c_end//3600)}:{int((c_end%3600)//60):02d}:{c_end%60:05.2f}"
                    ass_events.append(f"Dialogue: 0,{s_str},{e_str},TitleStyle,,0,0,0,Scroll up;{target_h};0;{t_speed};0,{ass_styled_text}")
            else:
                # \\an8 (top-center anchor) guarantees exact horizontal centering at pos_x and vertical placement at pos_y
                ass_events.append(f"Dialogue: 0,0:00:00.00,9:59:59.00,TitleStyle,,0,0,0,,{{\\an8\\pos({pos_x},{pos_y})}}{ass_styled_text}")

            with open(ass_file, "w", encoding="utf-8") as f:
                f.write(ass_header + "\n".join(ass_events) + "\n")

            title_ass_filter = format_ass_filter_path(ass_file)
            filter_parts.append(
                f"{current_v}{title_ass_filter}[v_after_txt]"
            )
            current_v = "[v_after_txt]"

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
        err_msg = proc.stderr or ""
        try:
            with open("render_err.log", "w", encoding="utf-8") as ef:
                ef.write(err_msg)
        except Exception:
            pass
        safe_preview = err_msg[:200].encode('ascii', errors='replace').decode('ascii')
        print(f"Render fallback triggered: {safe_preview}")
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
            "-fflags", "+genpts",
            "-avoid_negative_ts", "make_zero",
            str(out_p)
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", timeout=7200, **get_silent_kwargs())
        if proc.returncode != 0:
            # 1. First fallback: re-encoding via concat demuxer (supports unlimited episode count cleanly)
            cmd_list_reencode = [
                get_ffmpeg_path(),
                "-nostdin",
                "-y",
                "-fflags", "+genpts",
                "-avoid_negative_ts", "make_zero",
                "-f", "concat",
                "-safe", "0",
                "-i", str(list_file),
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "192k",
                str(out_p)
            ]
            proc_list_re = subprocess.run(cmd_list_reencode, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=7200, **get_silent_kwargs())
            if proc_list_re.returncode != 0 and len(video_paths) <= 60:
                # 2. Second fallback: filter_complex concat for mismatched dimensions
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

