"""
Flask Web Server & REST APIs for Khmer AI Drama Voice Translator & Movie Recap Studio (SN STUDIO V4.5)
"""
import os
import sys
import time
import json
import shutil
import asyncio
import subprocess
import threading
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any

from flask import Flask, request, jsonify, send_file, send_from_directory

# Resolve base dir for PyInstaller executable support
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent

STATIC_DIR = BASE_DIR / "static"

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="")

# Core Studio Modules & Engines
from tts_engine import get_available_voices, synthesize_khmer_speech
from translator import DramaTranslator, parse_srt_content
from pipeline import ProjectManager, SAMPLE_DRAMAS
from audio_processor import extract_audio_from_video, create_waveform_data, get_media_duration
from downloader import (
    download_video_from_url,
    get_supported_platforms_with_counts,
    DRAMA_CATALOG,
    get_drama_episodes,
    drama_downloader
)
from recap_engine import RecapEngine, VIRAL_KHMER_HOOKS
from batch_engine import batch_manager, EXPORTS_DIR
from video_processor import (
    merge_videos,
    split_video,
    batch_rename_files,
    compress_video
)
from license_engine import (
    check_current_device_license,
    activate_license_on_device,
    generate_license_key,
    get_machine_hwid,
    ADMIN_HISTORY_FILE
)
from update import check_for_updates, get_version_info

pm = ProjectManager()

Path("static").mkdir(parents=True, exist_ok=True)
Path("data/uploads").mkdir(parents=True, exist_ok=True)
Path("data/exports").mkdir(parents=True, exist_ok=True)
Path("cache").mkdir(parents=True, exist_ok=True)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,PUT,POST,DELETE,OPTIONS"
    return response


@app.route("/")
def index():
    return send_from_directory(str(STATIC_DIR), "index.html")


@app.route("/favicon.ico")
@app.route("/icon.ico")
def favicon():
    return send_from_directory(str(STATIC_DIR), "favicon.ico")


@app.route("/api/voices", methods=["GET"])
def get_voices():
    return jsonify({"voices": get_available_voices()})


@app.route("/api/voices/preview", methods=["POST"])
def preview_voice():
    data = request.get_json(force=True) or {}
    text = data.get("text", "សួស្តី")
    voice = data.get("voice", "piseth")
    rate = int(data.get("rate_percent", 0))
    pitch = int(data.get("pitch_hz", 0))

    try:
        sample_path = asyncio.run(synthesize_khmer_speech(
            text=text,
            voice=voice,
            rate_percent=rate,
            pitch_hz=pitch,
            use_cache=True
        ))
        return jsonify({"success": True, "audio_url": f"/media/{sample_path.replace(chr(92), '/')}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/samples", methods=["GET"])
def get_sample_list():
    return jsonify({"samples": SAMPLE_DRAMAS})


@app.route("/api/recap-hooks", methods=["GET"])
def get_recap_hooks():
    return jsonify({"hooks": VIRAL_KHMER_HOOKS})


@app.route("/api/projects/sample/<sample_key>", methods=["POST"])
def load_sample_drama(sample_key):
    try:
        project = pm.load_sample(sample_key)
        return jsonify({"success": True, "project": project})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/projects", methods=["GET"])
def list_projects():
    return jsonify({"projects": pm.list_projects()})


@app.route("/api/projects/new", methods=["POST"])
def create_new_project():
    title = request.form.get("title", "New Drama Project")
    mode = request.form.get("mode", "drama_dubbing")
    project = pm.create_project(title=title, mode=mode)
    return jsonify({"success": True, "project": project})


@app.route("/api/projects/<project_id>", methods=["GET"])
def get_project(project_id):
    project = pm.load_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    return jsonify({"project": project})


@app.route("/api/projects/<project_id>/save", methods=["POST"])
def save_project_data(project_id):
    project = pm.load_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    data = request.get_json(force=True) or {}
    project.update(data)
    pm.save_project(project)
    return jsonify({"success": True, "project": project})


@app.route("/api/projects/<project_id>/upload-video", methods=["POST"])
def upload_video(project_id):
    project = pm.load_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    proj_dir = Path(f"data/projects/{project_id}")
    proj_dir.mkdir(parents=True, exist_ok=True)
    
    file_ext = Path(file.filename).suffix.lower()
    video_dest = proj_dir / f"source_media{file_ext}"
    file.save(str(video_dest))

    audio_dest = proj_dir / "original_audio.wav"
    try:
        extract_audio_from_video(str(video_dest), str(audio_dest))
        project["video_file"] = str(video_dest)
        project["original_audio_file"] = str(audio_dest)
        project["duration"] = get_media_duration(str(video_dest))
        project["waveform"] = create_waveform_data(str(audio_dest))
        pm.save_project(project)
        return jsonify({"success": True, "project": project})
    except Exception as e:
        return jsonify({"error": f"Failed to process media file: {str(e)}"}), 500


@app.route("/api/projects/<project_id>/download-url", methods=["POST"])
def download_url_endpoint(project_id):
    project = pm.load_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    data = request.get_json(force=True) or {}
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "URL cannot be empty"}), 400

    proj_dir = Path(f"data/projects/{project_id}")
    proj_dir.mkdir(parents=True, exist_ok=True)

    try:
        res = download_video_from_url(url, output_dir=str(proj_dir))
        video_path = res["video_file"]
        audio_dest = proj_dir / "original_audio.wav"
        
        extract_audio_from_video(str(video_path), str(audio_dest))
        project["video_file"] = str(video_path)
        project["original_audio_file"] = str(audio_dest)
        project["title"] = res.get("title", project["title"])
        project["duration"] = res.get("duration") or get_media_duration(str(video_path))
        project["waveform"] = create_waveform_data(str(audio_dest))
        pm.save_project(project)

        return jsonify({"success": True, "project": project})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/projects/<project_id>/auto-transcribe", methods=["POST"])
def auto_transcribe_endpoint(project_id):
    try:
        project = pm.auto_transcribe_project(project_id)
        return jsonify({"success": True, "project": project, "dialogues_count": len(project.get("dialogues", []))})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/projects/<project_id>/separate-vocals", methods=["POST"])
def separate_vocals_endpoint(project_id):
    try:
        project = pm.separate_project_vocals(project_id)
        return jsonify({"success": True, "project": project, "bgm_file": project.get("isolated_bgm_file")})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/projects/<project_id>/inject-hook", methods=["POST"])
def inject_hook_endpoint(project_id):
    project = pm.load_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    data = request.get_json(force=True) or {}
    hook_text = data.get("hook_text", "")
    voice = data.get("voice", "piseth")

    if hook_text:
        project["dialogues"] = RecapEngine.inject_viral_hook(project.get("dialogues", []), hook_text, voice)
        pm.save_project(project)
        return jsonify({"success": True, "project": project})
    return jsonify({"error": "Hook text is empty"}), 400


@app.route("/api/projects/<project_id>/upload-srt", methods=["POST"])
def upload_srt(project_id):
    project = pm.load_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    content = file.read().decode("utf-8", errors="ignore")
    parsed_dialogues = parse_srt_content(content)
    
    project["dialogues"] = parsed_dialogues
    pm.save_project(project)
    return jsonify({"success": True, "dialogues_count": len(parsed_dialogues), "project": project})


@app.route("/api/projects/<project_id>/translate", methods=["POST"])
def translate_project_script(project_id):
    data = request.get_json(force=True) or {}
    mode = data.get("mode", "drama_dubbing")
    source_lang = data.get("source_lang", "auto")
    voice_override = data.get("voice_override")

    try:
        updated_project = asyncio.run(pm.translate_project(
            project_id=project_id,
            mode=mode,
            source_lang=source_lang,
            voice_override=voice_override
        ))
        return jsonify({"success": True, "project": updated_project})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/projects/<project_id>/generate-line-audio", methods=["POST"])
def generate_single_line_audio(project_id):
    project = pm.load_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    data = request.get_json(force=True) or {}
    line_index = int(data.get("line_index", 0))
    text_km = data.get("text_km", "")
    voice = data.get("voice", "piseth")
    rate = int(data.get("rate_percent", 0))
    pitch = int(data.get("pitch_hz", 0))

    proj_dir = Path(f"data/projects/{project_id}/voices")
    proj_dir.mkdir(parents=True, exist_ok=True)
    out_line_path = proj_dir / f"line_{line_index:04d}.mp3"

    try:
        audio_path = asyncio.run(synthesize_khmer_speech(
            text=text_km,
            voice=voice,
            rate_percent=rate,
            pitch_hz=pitch,
            output_path=str(out_line_path)
        ))
        
        dialogues = project.get("dialogues", [])
        if 0 <= line_index < len(dialogues):
            dialogues[line_index]["audio_file"] = audio_path
            dialogues[line_index]["voice"] = voice
            dialogues[line_index]["text_km"] = text_km
            dialogues[line_index]["rate_percent"] = rate
            dialogues[line_index]["pitch_hz"] = pitch
            pm.save_project(project)

        return jsonify({"success": True, "audio_url": f"/media/{audio_path.replace(chr(92), '/')}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/projects/<project_id>/generate-audio-all", methods=["POST"])
def generate_audio_all(project_id):
    try:
        updated_project = asyncio.run(pm.generate_project_audio(project_id))
        return jsonify({
            "success": True,
            "project": updated_project,
            "mixed_audio_url": f"/media/{updated_project['mixed_audio_file'].replace(chr(92), '/')}"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/projects/<project_id>/render-video", methods=["POST"])
def render_video_endpoint(project_id):
    burn_sub = request.args.get("burn_subtitles", "true").lower() == "true"
    aspect_ratio = request.args.get("aspect_ratio", "16:9")
    watermark = request.args.get("watermark", "")
    
    try:
        updated_project = pm.render_project_video_final(
            project_id=project_id,
            burn_subtitles=burn_sub,
            aspect_ratio=aspect_ratio,
            watermark_text=watermark
        )
        return jsonify({
            "success": True,
            "project": updated_project,
            "video_url": f"/media/{updated_project['output_video_file'].replace(chr(92), '/')}"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==========================================================================
# Automated Batch & Folder Processing Endpoints
# ==========================================================================
@app.route("/api/batch/upload", methods=["POST"])
def batch_upload_endpoint():
    """Upload multiple videos or whole folder for automated auto-dubbing."""
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    voice_mode = request.form.get("voice_mode", "auto")
    drama_mode = request.form.get("drama_mode", "drama_dubbing")
    aspect_ratio = request.form.get("aspect_ratio", "16:9")
    burn_subtitles = request.form.get("burn_subtitles", "true").lower() == "true"
    separate_bgm = request.form.get("separate_bgm", "true").lower() == "true"

    saved_paths = []
    upload_dir = Path("data/uploads/batch_temp")
    upload_dir.mkdir(parents=True, exist_ok=True)

    for f in files:
        if f.filename:
            dest = upload_dir / Path(f.filename).name
            f.save(str(dest))
            saved_paths.append(str(dest))

    # Add to queue and trigger worker
    added_items = batch_manager.add_files_to_queue(
        file_paths=saved_paths,
        voice_mode=voice_mode,
        drama_mode=drama_mode,
        aspect_ratio=aspect_ratio,
        burn_subtitles=burn_subtitles,
        separate_bgm=separate_bgm
    )
    batch_manager.start_batch_processing()

    return jsonify({"success": True, "added_count": len(added_items), "queue": batch_manager.get_queue_status()})


@app.route("/api/batch/status", methods=["GET"])
def batch_status_endpoint():
    """Get real-time batch queue processing status."""
    return jsonify({
        "is_processing": batch_manager.is_processing,
        "queue": batch_manager.get_queue_status()
    })


@app.route("/api/batch/clear", methods=["POST"])
def batch_clear_endpoint():
    batch_manager.clear_completed()
    return jsonify({"success": True, "queue": batch_manager.get_queue_status()})


@app.route("/api/open-export-folder", methods=["POST"])
def open_export_folder():
    """Open output folder in Windows File Explorer."""
    folder_p = EXPORTS_DIR.resolve()
    if sys.platform == "win32":
        try:
            os.startfile(str(folder_p))
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"success": True})


@app.route("/api/set-api-key", methods=["POST"])
def set_gemini_api_key():
    data = request.get_json(force=True) or {}
    key = data.get("api_key", "")
    pm.translator.set_api_key(key)
    os.environ["GEMINI_API_KEY"] = key
    return jsonify({"success": True, "message": "Cloud Engine Token updated successfully."})



# ==========================================================================
# License & Security REST APIs
# ==========================================================================
@app.route("/api/license/status", methods=["GET"])
def license_status_endpoint():
    """Check device license status & HWID."""
    info = check_current_device_license()
    return jsonify(info)


@app.route("/api/license/activate", methods=["POST"])
def license_activate_endpoint():
    """Activate license key on this device."""
    data = request.get_json(force=True) or {}
    key = data.get("license_key", "").strip()
    if not key:
        return jsonify({"success": False, "error": "សូមបញ្ចូល License Key"}), 400

    success, msg, record = activate_license_on_device(key)
    return jsonify({
        "success": success,
        "message": msg,
        "license": record
    })


@app.route("/api/admin/generate-key", methods=["POST"])
def admin_generate_key_endpoint():
    """Admin endpoint to generate client license keys."""
    data = request.get_json(force=True) or {}
    client_name = data.get("client_name", "Client_VIP")
    duration_days = int(data.get("duration_days", 30))
    hwid = data.get("hwid") or None
    plan = data.get("plan", "VIP_PRO")

    record = generate_license_key(client_name=client_name, duration_days=duration_days, hwid=hwid, plan=plan)
    return jsonify({"success": True, "key_record": record})


@app.route("/admin")
def admin_dashboard_page():
    """Serve Admin Key Generator Dashboard GUI."""
    return send_from_directory(str(STATIC_DIR), "admin.html")


@app.route("/api/admin/keys", methods=["GET"])
def admin_keys_list_endpoint():
    """Admin endpoint to list all generated keys."""
    if ADMIN_HISTORY_FILE.exists():
        try:
            with open(ADMIN_HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
            return jsonify({"success": True, "keys": history})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    return jsonify({"success": True, "keys": []})


@app.route("/api/admin/export-txt", methods=["GET"])
def admin_export_txt_endpoint():
    """Export all generated keys as a downloadable .txt file."""
    from license_engine import GENERATED_KEYS_LOG
    if not GENERATED_KEYS_LOG.exists():
        GENERATED_KEYS_LOG.write_text("# SN STUDIO - Generated Keys Log\n", encoding="utf-8")
    return send_file(str(GENERATED_KEYS_LOG.resolve()), as_attachment=True, download_name="SN_STUDIO_Generated_Keys.txt")


@app.route("/api/update/check", methods=["GET"])
def update_check_endpoint():
    """Check for latest studio version and patch notes."""
    return jsonify(check_for_updates())


# ==========================================================================
# Downloader Studio REST APIs
# ==========================================================================
@app.route("/api/downloader/platforms", methods=["GET"])
def downloader_platforms_endpoint():
    """Get list of supported drama download platforms."""
    return jsonify({"success": True, "platforms": get_supported_platforms_with_counts()})


@app.route("/api/downloader/catalog", methods=["GET"])
def downloader_catalog_endpoint():
    """Get list of catalog dramas with optional platform & search filters."""
    platform = request.args.get("platform", "all").lower()
    query = request.args.get("q", "").lower().strip()
    
    results = list(DRAMA_CATALOG)
    if platform and platform != "all":
        results = [d for d in results if d.get("platform_id") == platform]
    if query:
        results = [d for d in results if query in d.get("title", "").lower() or query in d.get("description", "").lower()]
        
    return jsonify({"success": True, "dramas": results, "total_count": len(results)})


@app.route("/api/downloader/analyze", methods=["POST"])
def downloader_analyze_endpoint():
    """Analyze drama URL or fetch drama episode manifest."""
    data = request.get_json(force=True) or {}
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"success": False, "error": "URL cannot be empty."}), 400
        
    try:
        res = drama_downloader.analyze_url(url)
        return jsonify(res)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/downloader/drama/<drama_id>", methods=["GET"])
def downloader_drama_detail_endpoint(drama_id):
    """Get single drama details with full episodes."""
    drama = next((d for d in DRAMA_CATALOG if d["id"] == drama_id), None)
    if not drama:
        return jsonify({"success": False, "error": "Drama not found"}), 404
        
    episodes = get_drama_episodes(drama)
    drama_downloader.current_drama = drama
    drama_downloader.episodes = episodes
    drama_downloader.stats["total"] = len(episodes)
    drama_downloader.stats["selected"] = len(episodes)
    drama_downloader.stats["completed"] = 0
    drama_downloader.stats["failed"] = 0
    drama_downloader.stats["locked"] = 0
    drama_downloader.stats["progress_percent"] = 0
    drama_downloader.add_log(f"Selected drama: '{drama['title']}' ({len(episodes)} episodes loaded).")
    
    return jsonify({
        "success": True,
        "drama": drama,
        "episodes": episodes,
        "stats": drama_downloader.stats
    })


@app.route("/api/downloader/download-episodes", methods=["POST"])
def downloader_download_episodes_endpoint():
    """Start batch download for selected episodes."""
    data = request.get_json(force=True) or {}
    episode_ids = data.get("episode_ids", [])
    save_location = data.get("save_location", "data/exports")
    save_poster = data.get("save_poster", True)
    
    res = drama_downloader.start_download_batch(episode_ids, save_location, save_poster)
    return jsonify(res)


@app.route("/api/downloader/status", methods=["GET"])
def downloader_status_endpoint():
    """Poll real-time downloader status, episodes state, and activity logs."""
    return jsonify({
        "is_downloading": drama_downloader.is_downloading,
        "drama": drama_downloader.current_drama,
        "episodes": drama_downloader.episodes,
        "logs": drama_downloader.logs,
        "stats": drama_downloader.stats
    })


@app.route("/api/downloader/stop", methods=["POST"])
def downloader_stop_endpoint():
    """Stop active download queue."""
    return jsonify(drama_downloader.stop_download())


@app.route("/api/downloader/clear-log", methods=["POST"])
def downloader_clear_log_endpoint():
    """Clear downloader activity log."""
    drama_downloader.logs = [f"[{time.strftime('%H:%M:%S')}] Activity log cleared."]
    return jsonify({"success": True})


# ==========================================================================
# System / Folder Picker & File Explorer REST APIs
# ==========================================================================
@app.route("/api/system/default-paths", methods=["GET"])
def system_default_paths_endpoint():
    """Return clean standard Drive C: and Drive D: paths for saving downloaded media."""
    drive_c = "C:/SN_Dramas"
    drive_d = "D:/SN_Dramas" if os.path.exists("D:/") else "C:/SN_Dramas"
    
    return jsonify({
        "success": True,
        "default": drive_d,
        "drive_c": drive_c,
        "drive_d": drive_d
    })


@app.route("/api/system/select-folder", methods=["POST", "GET"])
def system_select_folder_endpoint():
    """Pop native Windows folder picker dialog and return selected path."""
    data = {}
    if request.is_json:
        data = request.get_json(silent=True) or {}
    initial_dir = data.get("initial_dir", "")
    if not initial_dir or not os.path.exists(initial_dir):
        initial_dir = "D:/" if os.path.exists("D:/") else "C:/"
        
    chosen_path = None
    
    # Try subprocess Tkinter picker (clean, foreground topmost window)
    try:
        py_code = f"""
import os, sys
try:
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    init_dir = r'''{initial_dir}'''
    if not os.path.exists(init_dir):
        init_dir = 'D:/' if os.path.exists('D:/') else 'C:/'
    folder = filedialog.askdirectory(
        parent=root,
        title="Select Download Save Folder (Drive C: or Drive D:)",
        initialdir=init_dir
    )
    root.destroy()
    if folder:
        print("RESULT:" + folder)
except Exception:
    pass
"""
        proc = subprocess.run(
            [sys.executable, "-c", py_code],
            capture_output=True,
            text=True,
            timeout=120
        )
        for line in proc.stdout.splitlines():
            if line.startswith("RESULT:"):
                chosen_path = line[7:].strip().replace("\\", "/")
                break
    except Exception:
        pass

    # Fallback to PowerShell FolderBrowserDialog if Tkinter didn't return
    if not chosen_path and sys.platform == "win32":
        try:
            ps_code = f"""
            Add-Type -AssemblyName System.Windows.Forms
            $f = New-Object System.Windows.Forms.FolderBrowserDialog
            $f.Description = 'Select Download Save Folder (Drive C: or Drive D:)'
            $f.ShowNewFolderButton = $true
            if (Test-Path '{initial_dir}') {{
                $f.SelectedPath = '{initial_dir}'
            }}
            $owner = New-Object System.Windows.Forms.NativeWindow
            $owner.AssignHandle([System.Diagnostics.Process]::GetCurrentProcess().MainWindowHandle)
            $res = $f.ShowDialog($owner)
            if ($res -eq [System.Windows.Forms.DialogResult]::OK) {{
                Write-Output ("RESULT:" + $f.SelectedPath)
            }}
            """
            proc2 = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_code],
                capture_output=True,
                text=True,
                timeout=120
            )
            for line in proc2.stdout.splitlines():
                if "RESULT:" in line:
                    chosen_path = line.split("RESULT:", 1)[1].strip().replace("\\", "/")
                    break
        except Exception:
            pass

    if chosen_path:
        return jsonify({"success": True, "path": chosen_path})
    return jsonify({"success": False, "cancelled": True})


@app.route("/api/system/open-folder", methods=["POST"])
def system_open_folder_endpoint():
    """Open specified folder on the user's laptop using Windows Explorer."""
    data = request.get_json(force=True) or {}
    folder_path = data.get("path", "").strip()
    if not folder_path:
        folder_path = str(Path.home() / "Downloads" / "SN_Dramas")
        
    p = Path(folder_path)
    try:
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            
        if sys.platform == "win32":
            os.startfile(str(p))
        else:
            subprocess.Popen(["xdg-open", str(p)])
        return jsonify({"success": True, "path": str(p).replace("\\", "/")})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==========================================================================
# Power Tools REST APIs
# ==========================================================================
@app.route("/api/power/merge", methods=["POST"])
def power_merge_endpoint():
    """Merge multiple video files into one video."""
    data = request.get_json(force=True) or {}
    files = data.get("files", [])
    if len(files) < 2:
        return jsonify({"success": False, "error": "At least 2 video files are required for merging."}), 400
        
    out_file = f"data/exports/merged_drama_{int(time.time())}.mp4"
    try:
        res_p = merge_videos(files, out_file)
        return jsonify({"success": True, "output_file": res_p, "download_url": f"/media/{res_p.replace(chr(92), '/')}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/power/split", methods=["POST"])
def power_split_endpoint():
    """Split video file into parts."""
    data = request.get_json(force=True) or {}
    video_path = data.get("video_path", "")
    chunk_sec = int(data.get("chunk_duration_sec", 60))
    if not video_path or not Path(video_path).exists():
        return jsonify({"success": False, "error": "Invalid source video path."}), 400
        
    out_dir = f"data/exports/split_{int(time.time())}"
    try:
        parts = split_video(video_path, chunk_sec, out_dir)
        return jsonify({"success": True, "parts_count": len(parts), "parts": parts})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/power/rename", methods=["POST"])
def power_rename_endpoint():
    """Batch rename files."""
    data = request.get_json(force=True) or {}
    files = data.get("files", [])
    prefix = data.get("prefix", "Drama_EP")
    start_num = int(data.get("start_num", 1))
    
    try:
        res = batch_rename_files(files, prefix, start_num)
        return jsonify({"success": True, "results": res})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/power/compress", methods=["POST"])
def power_compress_endpoint():
    """Compress video file."""
    data = request.get_json(force=True) or {}
    video_path = data.get("video_path", "")
    crf = int(data.get("crf", 26))
    preset = data.get("preset", "fast")
    target_height = data.get("target_height")
    if target_height:
        target_height = int(target_height)
        
    if not video_path or not Path(video_path).exists():
        return jsonify({"success": False, "error": "Invalid video path."}), 400
        
    out_file = f"data/exports/compressed_{Path(video_path).stem}_{int(time.time())}.mp4"
    try:
        res_p = compress_video(video_path, out_file, crf, preset, target_height)
        return jsonify({"success": True, "output_file": res_p, "download_url": f"/media/{res_p.replace(chr(92), '/')}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==========================================================================
# 1-Click Automated Video Dubbing & Status Polling
# ==========================================================================
video_auto_tasks: Dict[str, Dict[str, Any]] = {}

@app.route("/api/projects/auto-dub-video", methods=["POST"])
def auto_dub_video_endpoint():
    """
    1-Click Automated Video Dubbing (Chinese/Multilingual Video -> Khmer Speech & Video).
    Accepts video file upload or local filepath.
    """
    mode = request.form.get("drama_mode", "drama_dubbing")
    source_lang = request.form.get("source_lang", "auto")
    voice_override = request.form.get("voice_override", "auto")
    aspect_ratio = request.form.get("aspect_ratio", "16:9")
    burn_subtitles = request.form.get("burn_subtitles", "true").lower() == "true"
    
    saved_video_path = None
    original_filename = "drama_video.mp4"

    if "file" in request.files and request.files["file"].filename:
        file = request.files["file"]
        original_filename = file.filename
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        unique_name = f"{int(time.time())}_{Path(original_filename).name}"
        dest = upload_dir / unique_name
        file.save(str(dest))
        saved_video_path = str(dest)
    elif request.is_json:
        data = request.get_json(force=True) or {}
        saved_video_path = data.get("filepath")
        if saved_video_path:
            original_filename = Path(saved_video_path).name
            mode = data.get("drama_mode", mode)
            source_lang = data.get("source_lang", source_lang)
            voice_override = data.get("voice_override", voice_override)
            aspect_ratio = data.get("aspect_ratio", aspect_ratio)
            burn_subtitles = data.get("burn_subtitles", burn_subtitles)

    if not saved_video_path or not Path(saved_video_path).exists():
        return jsonify({"success": False, "error": "No valid video file uploaded or provided."}), 400

    task_id = str(uuid.uuid4())[:8]
    video_auto_tasks[task_id] = {
        "task_id": task_id,
        "filename": original_filename,
        "status": "processing",
        "progress": 5,
        "step_km": "កំពុងរៀបចំប្រព័ន្ធកែច្នៃ...",
        "step_en": "Initializing pipeline...",
        "project": None,
        "error": None
    }

    def _worker(t_id: str, v_path: str, m: str, sl: str, vo: str, ar: str, bs: bool):
        def _prog_cb(pct: int, km: str, en: str):
            if t_id in video_auto_tasks:
                video_auto_tasks[t_id]["progress"] = pct
                video_auto_tasks[t_id]["step_km"] = km
                video_auto_tasks[t_id]["step_en"] = en

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                res_proj = loop.run_until_complete(pm.process_video_pipeline(
                    video_path=v_path,
                    title=f"Dubbed_{Path(v_path).stem}",
                    mode=m,
                    source_lang=sl,
                    voice_override=vo,
                    aspect_ratio=ar,
                    burn_subtitles=bs,
                    progress_callback=_prog_cb
                ))
            finally:
                loop.close()

            if t_id in video_auto_tasks:
                video_auto_tasks[t_id]["status"] = "completed"
                video_auto_tasks[t_id]["progress"] = 100
                video_auto_tasks[t_id]["step_km"] = "រួចរាល់ ១០០% (ជោគជ័យ!)"
                video_auto_tasks[t_id]["step_en"] = "Completed successfully!"
                video_auto_tasks[t_id]["project"] = res_proj
        except Exception as e:
            print(f"Auto dubbing worker error: {e}")
            if t_id in video_auto_tasks:
                video_auto_tasks[t_id]["status"] = "failed"
                video_auto_tasks[t_id]["error"] = str(e)
                video_auto_tasks[t_id]["step_km"] = f"មានបញ្ហា: {str(e)}"
                video_auto_tasks[t_id]["step_en"] = f"Error: {str(e)}"

    threading.Thread(
        target=_worker,
        args=(task_id, saved_video_path, mode, source_lang, voice_override, aspect_ratio, burn_subtitles),
        daemon=True
    ).start()

    return jsonify({
        "success": True,
        "task_id": task_id,
        "message": "Video translation task started successfully."
    })


@app.route("/api/projects/auto-dub-status/<task_id>", methods=["GET"])
def auto_dub_status_endpoint(task_id):
    task = video_auto_tasks.get(task_id)
    if not task:
        return jsonify({"success": False, "error": "Task not found"}), 404

    resp = {
        "success": True,
        "task_id": task["task_id"],
        "filename": task.get("filename"),
        "status": task.get("status"),
        "progress": task.get("progress", 0),
        "step_km": task.get("step_km", ""),
        "step_en": task.get("step_en", ""),
        "error": task.get("error")
    }
    if task.get("status") == "completed" and task.get("project"):
        proj = task["project"]
        resp["project"] = proj
        out_vid = proj.get("output_video_file") or ""
        out_aud = proj.get("mixed_audio_file") or ""
        resp["video_url"] = f"/media/{out_vid.replace(chr(92), '/')}" if out_vid else ""
        resp["mixed_audio_url"] = f"/media/{out_aud.replace(chr(92), '/')}" if out_aud else ""

    return jsonify(resp)


@app.route("/api/projects/open-folder", methods=["POST"])
def open_project_folder_endpoint():
    data = request.get_json(force=True) or {}
    target_path = data.get("path")
    if not target_path:
        target_path = str(Path("data/exports").resolve())
    else:
        p = Path(target_path)
        if p.is_file():
            target_path = str(p.parent.resolve())
        else:
            target_path = str(p.resolve())

    if sys.platform == "win32":
        try:
            os.startfile(target_path)
            return jsonify({"success": True, "opened_path": target_path})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    return jsonify({"success": True, "opened_path": target_path})


@app.route("/media/<path:filename>")
def serve_media(filename):
    file_path = Path(filename)
    if not file_path.exists():
        return jsonify({"error": "Media file not found"}), 404
        
    return send_file(str(file_path.resolve()), conditional=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
