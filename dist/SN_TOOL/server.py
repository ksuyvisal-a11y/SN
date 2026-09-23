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
import re
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
from audio_processor import extract_audio_from_video, create_waveform_data, get_media_duration, get_silent_kwargs
from downloader import (
    download_video_from_url,
    get_supported_platforms_with_counts,
    DRAMA_CATALOG,
    get_drama_episodes,
    drama_downloader,
    find_authentic_episode_video
)
import hongguo_db
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


@app.route("/static/<path:filename>")
def serve_static_alias(filename):
    """Ensure /static/ prefix always resolves properly to STATIC_DIR."""
    return send_from_directory(str(STATIC_DIR), filename)


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
    if not voice_override or voice_override == "auto":
        cfg = load_stored_story_config()
        if cfg.get("auto_multi_voice") is not False or cfg.get("khmer_voice") == "multi":
            voice_override = "multi"
        else:
            voice_override = cfg.get("khmer_voice", "multi")

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
    burn_sub = request.args.get("burn_subtitles", "false").lower() in ("true", "1", "yes")
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

    voice_mode = request.form.get("voice_mode", "piseth")
    if voice_mode in ("auto", "", None):
        cfg = load_stored_story_config()
        voice_mode = cfg.get("khmer_voice", "piseth") if not cfg.get("auto_multi_voice", False) else "auto_multi"
    drama_mode = request.form.get("drama_mode", "drama_dubbing")
    aspect_ratio = request.form.get("aspect_ratio", "16:9")
    cfg = load_stored_story_config()
    burn_sub_default = "true" if cfg.get("subtitle_mode", "none") == "burn" else "false"
    burn_subtitles = request.form.get("burn_subtitles", burn_sub_default).lower() in ("true", "1", "yes")
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


AI_CONFIG_FILE = Path("data/ai_provider_config.json")
STORY_CONFIG_FILE = Path("data/story_config.json")

def load_stored_ai_config() -> dict:
    if AI_CONFIG_FILE.exists():
        try:
            with open(AI_CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                keys = cfg.get("keys", [])
                valid_gemini = [k.strip() for k in keys if str(k).strip().startswith("AIzaSy")]
                if valid_gemini:
                    pm.translator.set_api_keys(valid_gemini)
                    os.environ["GEMINI_API_KEY"] = "\n".join(valid_gemini)
                else:
                    pm.translator.set_api_keys([])

                groq_pool = cfg.get("groq_keys", [])
                if isinstance(groq_pool, list) and groq_pool:
                    pm.translator.groq_keys = [k.strip() for k in groq_pool if k and str(k).startswith("gsk_")]
                groq_k = cfg.get("groq_api_key", "").strip()
                if groq_k:
                    pm.translator.groq_api_key = groq_k
                    os.environ["GROQ_API_KEY"] = groq_k
                return cfg
        except Exception as e:
            print(f"Error loading AI config: {e}")
    return {
        "engine": "auto",
        "groq_api_key": "",
        "gemini_api_key": "",
        "keys": [],
        "keys_raw": "",
        "model": "llama-3.3-70b-versatile",
        "temperature": 0.3,
        "prompt_style": "drama_dubbing"
    }

def load_stored_story_config() -> dict:
    if STORY_CONFIG_FILE.exists():
        try:
            with open(STORY_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading story config: {e}")
    return {
        "khmer_voice": "piseth",
        "auto_multi_voice": True,
        "source_lang": "auto",
        "whisper_model": "medium",
        "aspect_ratio": "9:16",
        "subtitle_mode": "none",
        "dubbing_mode": "smart_bgm",
        "ducking_volume": "0.35",
        "speech_boost_db": 2.5
    }

# Initial load on server start
stored_ai_cfg = load_stored_ai_config()
stored_story_cfg = load_stored_story_config()


@app.route("/api/set-api-key", methods=["POST"])
def set_gemini_api_key():
    data = request.get_json(force=True) or {}
    key = data.get("api_key", "").strip()
    keys = [k.strip() for k in key.replace(",", "\n").splitlines() if k.strip()]
    valid_gemini = [k for k in keys if k.startswith("AIzaSy")]
    pm.translator.set_api_keys(valid_gemini)
    if valid_gemini:
        os.environ["GEMINI_API_KEY"] = "\n".join(valid_gemini)
    return jsonify({"success": True, "message": "API keys updated."})


@app.route("/api/ai-config", methods=["GET"])
def get_ai_config_endpoint():
    cfg = load_stored_ai_config()
    safe_cfg = {
        "engine": cfg.get("engine", "auto"),
        "gemini_api_key": cfg.get("gemini_api_key", ""),
        "keys": cfg.get("keys", []),
        "keys_raw": cfg.get("keys_raw", "\n".join(cfg.get("keys", []))),
        "model": cfg.get("model", "qwen/qwen3.8-27b"),
        "temperature": cfg.get("temperature", 0.3),
        "prompt_style": cfg.get("prompt_style", "drama_dubbing")
    }
    return jsonify({
        "success": True,
        "config": safe_cfg,
        "active_keys_count": len([k for k in cfg.get("keys", []) if k.startswith("AIzaSy")]),
        "keys_raw": cfg.get("keys_raw", "\n".join(cfg.get("keys", [])))
    })


@app.route("/api/set-ai-config", methods=["POST"])
def set_ai_config_endpoint():
    data = request.get_json(force=True) or {}
    keys_raw = data.get("keys_raw", "")
    keys = data.get("keys", [])
    if not keys and keys_raw:
        keys = [k.strip() for k in keys_raw.replace(",", "\n").splitlines() if k.strip()]
    if not keys_raw and keys:
        keys_raw = "\n".join(keys)

    existing_cfg = load_stored_ai_config()
    groq_api_key = existing_cfg.get("groq_api_key", "")
    groq_keys = existing_cfg.get("groq_keys", [])

    gemini_api_key = data.get("gemini_api_key", "").strip()
    if gemini_api_key and gemini_api_key not in keys:
        keys.insert(0, gemini_api_key)

    engine = data.get("engine", "auto")
    model = data.get("model", "qwen/qwen3.8-27b")
    try:
        temperature = float(data.get("temperature", 0.3))
    except Exception:
        temperature = 0.3
    prompt_style = data.get("prompt_style", "drama_dubbing")

    cfg = {
        "engine": engine,
        "groq_api_key": groq_api_key,
        "groq_keys": groq_keys,
        "gemini_api_key": gemini_api_key,
        "keys": keys,
        "keys_raw": keys_raw,
        "model": model,
        "temperature": temperature,
        "prompt_style": prompt_style
    }

    AI_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(AI_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

    valid_gemini = [k for k in keys if k.startswith("AIzaSy")]
    pm.translator.set_api_keys(valid_gemini)
    if valid_gemini:
        os.environ["GEMINI_API_KEY"] = "\n".join(valid_gemini)

    pm.translator.groq_api_key = groq_api_key
    pm.translator.groq_keys = groq_keys
    if groq_api_key:
        os.environ["GROQ_API_KEY"] = groq_api_key

    safe_cfg = {
        "engine": engine,
        "gemini_api_key": gemini_api_key,
        "keys": keys,
        "keys_raw": keys_raw,
        "model": model,
        "temperature": temperature,
        "prompt_style": prompt_style
    }

    return jsonify({
        "success": True,
        "config": safe_cfg,
        "message": "AI Studio Engine configuration saved successfully."
    })


@app.route("/api/drama-dictionary", methods=["GET", "POST"])
def drama_dictionary_endpoint():
    dict_file = Path("data/drama_dictionary.json")
    if request.method == "POST":
        data = request.get_json(force=True) or {}
        entries = data.get("dictionary", data)
        if isinstance(entries, dict):
            dict_file.parent.mkdir(parents=True, exist_ok=True)
            with open(dict_file, "w", encoding="utf-8") as f:
                json.dump(entries, f, ensure_ascii=False, indent=2)
            return jsonify({"success": True, "dictionary": entries, "count": len(entries)})
        return jsonify({"success": False, "error": "Invalid dictionary format. Expected JSON object."}), 400

    # GET
    if dict_file.exists():
        try:
            with open(dict_file, "r", encoding="utf-8") as f:
                return jsonify({"success": True, "dictionary": json.load(f)})
        except Exception:
            pass
    return jsonify({"success": True, "dictionary": {}})


@app.route("/api/check-keys", methods=["POST"])
def check_keys_live_endpoint():
    data = request.get_json(force=True) or {}
    keys_raw = data.get("keys_raw", "")
    keys = data.get("keys", [])
    if not keys and keys_raw:
        keys = [k.strip() for k in keys_raw.replace(",", "\n").splitlines() if k.strip()]

    if not keys:
        return jsonify({"success": False, "error": "No API keys provided to check.", "total": 0, "valid": 0})

    results = []
    valid_count = 0

    for idx, key in enumerate(keys, start=1):
        masked = key[:6] + "..." + key[-4:] if len(key) > 10 else key
        status = "unknown"
        is_valid = False
        message = ""

        try:
            from google import genai
            client = genai.Client(api_key=key)
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents="test",
                config={"max_output_tokens": 2}
            )
            is_valid = True
            status = "active"
            message = "Live (200 OK)"
            valid_count += 1
        except Exception as err:
            err_str = str(err)
            if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
                status = "rate_limited"
                message = "Rate Limited (429)"
            elif any(token in err_str for token in ("401", "UNAUTHENTICATED", "API_KEY_INVALID", "400", "ACCESS_TOKEN")):
                status = "invalid"
                message = "Invalid Key (Need AIzaSy...)"
            else:
                status = "error"
                message = "Auth Failed"

        results.append({
            "index": idx,
            "key_masked": masked,
            "status": status,
            "valid": is_valid,
            "message": message
        })

    return jsonify({
        "success": True,
        "total": len(keys),
        "valid": valid_count,
        "results": results
    })


@app.route("/api/story-config", methods=["GET", "POST"])
def get_story_config_endpoint():
    if request.method == "POST":
        return set_story_config_endpoint()
    cfg = load_stored_story_config()
    ai_cfg = load_stored_ai_config()
    engine_name = ai_cfg.get("engine", "gemini_pool")
    if engine_name == "free_ai":
        provider_display = "Free AI (g4f)"
    elif engine_name == "google_free":
        provider_display = "Google Translate Built-in"
    elif engine_name == "gemini_pro":
        provider_display = "Gemini 2.5 Pro"
    else:
        provider_display = "Gemini API (Key Pool)"
        
    cfg["ai_provider_display"] = provider_display
    return jsonify({
        "success": True,
        "config": cfg
    })


@app.route("/api/set-story-config", methods=["POST"])
def set_story_config_endpoint():
    data = request.get_json(force=True) or {}
    cfg = load_stored_story_config()
    cfg.update(data)

    # Keep auto_multi_voice and khmer_voice synchronized
    if cfg.get("khmer_voice") == "multi":
        cfg["auto_multi_voice"] = True
    elif cfg.get("khmer_voice") in ("piseth", "sreymom"):
        cfg["auto_multi_voice"] = False

    # Sanitize ducking_volume so it is never empty or invalid
    raw_duck = str(cfg.get("ducking_volume", "")).strip()
    try:
        val = float(raw_duck)
        if val < 0:
            cfg["ducking_volume"] = "0.35"
        else:
            cfg["ducking_volume"] = f"{val:.2f}"
    except (ValueError, TypeError):
        cfg["ducking_volume"] = "0.35"

    STORY_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STORY_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

    return jsonify({
        "success": True,
        "message": "Story settings saved successfully!",
        "config": cfg
    })



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


@app.route("/api/downloader/categories", methods=["GET"])
def downloader_categories_endpoint():
    """Get list of Hongguo drama categories."""
    return jsonify({"success": True, "categories": hongguo_db.get_categories_list()})


@app.route("/api/downloader/catalog", methods=["GET"])
def downloader_catalog_endpoint():
    """Get list of catalog dramas with optional platform, category, pagination & search filters."""
    platform = request.args.get("platform", "all").lower()
    category = request.args.get("category", "all").lower()
    query = request.args.get("q", "").strip()
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 60))
    offset = max(0, (page - 1) * limit)

    dramas, total_count = hongguo_db.query_dramas(
        category=category if category != "all" else None,
        query=query if query else None,
        platform=platform if platform != "all" else None,
        limit=limit,
        offset=offset
    )

    return jsonify({
        "success": True,
        "dramas": dramas,
        "total_count": total_count,
        "page": page,
        "limit": limit,
        "has_more": (offset + len(dramas)) < total_count
    })


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
    """Get single drama details with full episodes and rich story profile."""
    drama = hongguo_db.get_drama_by_id(drama_id)
    if not drama:
        drama = next((d for d in DRAMA_CATALOG if d.get("id") == drama_id), None)
    if not drama and drama_downloader.current_drama and drama_downloader.current_drama.get("id") == drama_id:
        drama = drama_downloader.current_drama

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

    return jsonify({
        "success": True,
        "drama": drama,
        "episodes": episodes,
        "stats": drama_downloader.stats
    })


@app.route("/api/downloader/preview/<drama_id>", methods=["GET"])
def downloader_preview_endpoint(drama_id):
    """Get authentic preview video for a drama to play directly in 9:16 monitor."""
    ep_num = request.args.get("ep", 1, type=int)
    drama = hongguo_db.get_drama_by_id(drama_id)
    if not drama and drama_downloader.current_drama:
        if str(drama_downloader.current_drama.get("id")) == str(drama_id):
            drama = drama_downloader.current_drama

    # 1. Check if active episodes manifest has a genuine video file for this episode
    if drama_downloader.episodes:
        for ep in drama_downloader.episodes:
            if ep.get("episode_number") == ep_num or ep.get("episode_num") == ep_num:
                if ep.get("video_url") and ep.get("filepath") and Path(ep["filepath"]).exists():
                    return jsonify({
                        "success": True,
                        "video_url": ep["video_url"],
                        "title": ep.get("title") or (drama.get("title") if drama else f"Episode {ep_num}"),
                        "poster": drama.get("poster") if drama else "posters/poster_sample_ceo.jpg",
                        "episode": ep_num
                    })

    # 2. Check if authentic video file exists in save location or imported folder
    auth_src = find_authentic_episode_video(drama, ep_num)
    if auth_src and auth_src.exists():
        rel_or_abs = str(auth_src.resolve()).replace("\\", "/")
        return jsonify({
            "success": True,
            "video_url": f"/media/{rel_or_abs}",
            "title": drama.get("title") if drama else "Hongguo Short Drama",
            "poster": drama.get("poster") if drama else "posters/poster_sample_ceo.jpg",
            "episode": ep_num
        })

    # Do NOT return a fake/unrelated video!
    return jsonify({
        "success": False,
        "error": "no_video",
        "message": f"មិនទាន់មានវីដេអូសម្រាប់ភាគ {ep_num} នៅលើកុំព្យូទ័រទេ",
        "poster": drama.get("poster") if drama else "posters/poster_sample_ceo.jpg",
        "episode": ep_num
    }), 404


@app.route("/api/downloader/import-folder", methods=["POST", "GET"])
def downloader_import_folder_endpoint():
    """
    Import an authentic local short drama folder containing downloaded episode video files.
    If folder_path is not provided, opens native Windows folder chooser dialog.
    """
    folder_path = ""
    if request.is_json:
        data = request.get_json(silent=True) or {}
        folder_path = data.get("folder_path", "").strip()
    elif request.form.get("folder_path"):
        folder_path = request.form.get("folder_path", "").strip()

    if not folder_path:
        folder_path = open_native_windows_folder_dialog(
            title="ជ្រើសរើស Folder រឿងភាគដែលបានទាញយក (Select Downloaded Drama Folder)"
        )
        if not folder_path:
            return jsonify({"success": False, "cancelled": True, "message": "បានបោះបង់ការជ្រើសរើស Folder"})

    res = drama_downloader.import_drama_from_folder(folder_path)
    return jsonify(res)


@app.route("/api/downloader/send-to-studio", methods=["POST"])
def downloader_send_to_studio_endpoint():
    """Send an authentic downloaded or imported episode video directly to AI Studio Dubber."""
    data = request.get_json(force=True) or {}
    filepath = data.get("filepath", "").strip()
    filename = data.get("filename", "")
    drama_title = data.get("drama_title", "")

    if not filepath or not Path(filepath).exists():
        return jsonify({"success": False, "error": "Video file path does not exist on disk"}), 400

    p = Path(filepath)
    sz = p.stat().st_size
    sz_mb = f"{sz / (1024 * 1024):.1f}"

    return jsonify({
        "success": True,
        "filepath": str(p.resolve()).replace("\\", "/"),
        "filename": filename or p.name,
        "size_mb": sz_mb,
        "drama_title": drama_title or p.stem,
        "video_url": f"/media/{str(p.resolve()).replace(chr(92), '/')}"
    })


@app.route("/api/downloader/download-episodes", methods=["POST"])
def downloader_download_episodes_endpoint():
    """Start batch download for selected episodes."""
    data = request.get_json(force=True) or {}
    episode_ids = data.get("episode_ids", [])
    save_location = data.get("save_location") or ("D:/SN_Dramas" if os.path.exists("D:/") else "C:/SN_Dramas")
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


APP_ICON_PATH = str(Path(__file__).resolve().parent / "icon.ico").replace("\\", "/")
if not os.path.exists(APP_ICON_PATH):
    APP_ICON_PATH = str(Path(__file__).resolve().parent / "static" / "favicon.ico").replace("\\", "/")

MODERN_FOLDER_PICKER_CS = """
using System;
using System.IO;
using System.Runtime.InteropServices;

[ComImport]
[Guid("00000114-0000-0000-C000-000000000046")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IOleWindow {
    [PreserveSig] int GetWindow(out IntPtr phwnd);
    [PreserveSig] int ContextSensitiveHelp(bool fEnterMode);
}

[ComImport]
[Guid("43826D1E-E718-42EE-BC55-A1E261C37BFE")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IShellItem {
    void BindToHandler();
    void GetParent();
    void GetDisplayName(uint sigdnName, [MarshalAs(UnmanagedType.LPWStr)] out string ppszName);
    void GetAttributes();
    void Compare();
}

[ComImport]
[Guid("973510DB-7D7F-452B-8975-74A85828D354")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IFileDialogEvents {
    [PreserveSig] int OnFileOk(IntPtr pfd);
    [PreserveSig] int OnFolderChanging(IntPtr pfd, IntPtr psiFolder);
    [PreserveSig] int OnFolderChange(IntPtr pfd);
    [PreserveSig] int OnSelectionChange(IntPtr pfd);
    [PreserveSig] int OnShareViolation(IntPtr pfd, IntPtr psi, out int pResponse);
    [PreserveSig] int OnTypeChange(IntPtr pfd);
    [PreserveSig] int OnOverwrite(IntPtr pfd, IntPtr psi, out int pResponse);
}

[ComImport]
[Guid("DC1C5A9C-E88A-4dde-A5A1-60F82A20AEF7")]
public class FileOpenDialog { }

[ComImport]
[Guid("42f85136-db7e-439c-85f1-e4075d135fc8")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IFileOpenDialog {
    [PreserveSig] int Show(IntPtr parent);
    void SetFileTypes();
    void SetFileTypeIndex();
    void GetFileTypeIndex();
    void Advise(IFileDialogEvents pfde, out uint pdwCookie);
    void Unadvise(uint dwCookie);
    void SetOptions(uint fos);
    void GetOptions(out uint fos);
    void SetDefaultFolder(IShellItem psi);
    void SetFolder(IShellItem psi);
    void GetFolder(out IShellItem ppsi);
    void GetCurrentSelection(out IShellItem ppsi);
    void SetFileName([MarshalAs(UnmanagedType.LPWStr)] string pszName);
    void GetFileName([MarshalAs(UnmanagedType.LPWStr)] out string pszName);
    void SetTitle([MarshalAs(UnmanagedType.LPWStr)] string pszTitle);
    void SetOkButtonLabel([MarshalAs(UnmanagedType.LPWStr)] string pszText);
    void SetFileNameLabel([MarshalAs(UnmanagedType.LPWStr)] string pszLabel);
    void GetResult(out IShellItem ppsi);
    void AddPlace();
    void SetDefaultExtension();
    void Close();
    void SetClientGuid();
    void ClearClientData();
    void SetFilter();
    void GetResults();
    void GetSelectedItems();
}

public class DialogEventHandler : IFileDialogEvents {
    private object _dialog;
    private string _iconPath;
    public DialogEventHandler(object dialog, string iconPath) {
        _dialog = dialog;
        _iconPath = iconPath;
    }

    public int OnFolderChange(IntPtr pfd) {
        try {
            var ole = _dialog as IOleWindow;
            if (ole != null) {
                IntPtr hwnd;
                if (ole.GetWindow(out hwnd) == 0) {
                    ModernFolderPicker.ApplyStyleAndIcon(hwnd, _iconPath);
                }
            }
        } catch { }
        return 0;
    }

    public int OnFileOk(IntPtr pfd) { return 0; }
    public int OnFolderChanging(IntPtr pfd, IntPtr psiFolder) {
        try {
            var ole = _dialog as IOleWindow;
            if (ole != null) {
                IntPtr hwnd;
                if (ole.GetWindow(out hwnd) == 0) {
                    ModernFolderPicker.ApplyStyleAndIcon(hwnd, _iconPath);
                }
            }
        } catch { }
        return 0;
    }
    public int OnSelectionChange(IntPtr pfd) { return 0; }
    public int OnShareViolation(IntPtr pfd, IntPtr psi, out int pResponse) { pResponse = 0; return 0; }
    public int OnTypeChange(IntPtr pfd) { return 0; }
    public int OnOverwrite(IntPtr pfd, IntPtr psi, out int pResponse) { pResponse = 0; return 0; }
}

public class ModernFolderPicker {
    [DllImport("user32.dll")]
    public static extern bool SetProcessDpiAwarenessContext(IntPtr dpiContext);

    [DllImport("shcore.dll")]
    public static extern int SetProcessDpiAwareness(int awareness);

    [DllImport("user32.dll")]
    public static extern bool SetProcessDPIAware();

    [DllImport("user32.dll")]
    private static extern int GetSystemMetrics(int nIndex);

    private const int SM_CXICON = 11;
    private const int SM_CYICON = 12;
    private const int SM_CXSMICON = 49;
    private const int SM_CYSMICON = 50;

    public static void EnableHighDpi() {
        try {
            // Per-Monitor V2 High DPI Awareness (eliminates blurriness on 125%, 150%, 175%, 200% scaling!)
            if (!SetProcessDpiAwarenessContext((IntPtr)(-4))) {
                SetProcessDpiAwareness(2);
            }
        } catch {
            try {
                SetProcessDPIAware();
            } catch { }
        }
    }

    [DllImport("shell32.dll")]
    private static extern int SHCreateItemFromParsingName(
        [MarshalAs(UnmanagedType.LPWStr)] string pszPath,
        IntPtr pbc,
        [In, MarshalAs(UnmanagedType.LPStruct)] Guid riid,
        [Out, MarshalAs(UnmanagedType.Interface)] out IShellItem ppv);

    [DllImport("dwmapi.dll")]
    public static extern int DwmSetWindowAttribute(IntPtr hwnd, int attr, ref int attrValue, int attrSize);

    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern IntPtr SendMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);

    [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    public static extern IntPtr LoadImage(IntPtr hinst, string lpszName, uint uType, int cxDesired, int cyDesired, uint fuLoad);

    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();

    public const int DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19;
    public const int DWMWA_USE_IMMERSIVE_DARK_MODE = 20;

    private const uint WM_SETICON = 0x0080;
    private const uint IMAGE_ICON = 1;
    private const uint LR_LOADFROMFILE = 0x00000010;

    public static void ApplyStyleAndIcon(IntPtr hwnd, string iconPath) {
        if (hwnd == IntPtr.Zero) return;
        try {
            int darkMode = 1;
            DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ref darkMode, sizeof(int));
            DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1, ref darkMode, sizeof(int));

            if (!string.IsNullOrEmpty(iconPath) && File.Exists(iconPath)) {
                int cxSmall = GetSystemMetrics(SM_CXSMICON);
                int cySmall = GetSystemMetrics(SM_CYSMICON);
                int cxBig = GetSystemMetrics(SM_CXICON);
                int cyBig = GetSystemMetrics(SM_CYICON);
                if (cxSmall <= 0) cxSmall = 16;
                if (cySmall <= 0) cySmall = 16;
                if (cxBig <= 0) cxBig = 32;
                if (cyBig <= 0) cyBig = 32;

                IntPtr hSmall = LoadImage(IntPtr.Zero, iconPath, IMAGE_ICON, cxSmall, cySmall, LR_LOADFROMFILE);
                if (hSmall != IntPtr.Zero) {
                    SendMessage(hwnd, WM_SETICON, (IntPtr)0, hSmall);
                }
                IntPtr hBig = LoadImage(IntPtr.Zero, iconPath, IMAGE_ICON, cxBig, cyBig, LR_LOADFROMFILE);
                if (hBig != IntPtr.Zero) {
                    SendMessage(hwnd, WM_SETICON, (IntPtr)1, hBig);
                }
            }
        } catch { }
    }

    public static string ShowDialog(string initialPath, string title, string iconPath, IntPtr owner) {
        var dialog = (IFileOpenDialog)new FileOpenDialog();
        uint FOS_PICKFOLDERS = 0x00000020;
        uint FOS_FORCEFILESYSTEM = 0x00000040;
        uint FOS_NOVALIDATE = 0x00000100;
        uint FOS_NOTESTFILECREATE = 0x00010000;
        uint FOS_PATHMUSTEXIST = 0x00000800;
        dialog.SetOptions(FOS_PICKFOLDERS | FOS_FORCEFILESYSTEM | FOS_NOVALIDATE | FOS_NOTESTFILECREATE | FOS_PATHMUSTEXIST);

        if (!string.IsNullOrEmpty(title)) {
            dialog.SetTitle(title);
            dialog.SetOkButtonLabel("Select Folder");
        }

        if (!string.IsNullOrEmpty(initialPath) && Directory.Exists(initialPath)) {
            IShellItem folderItem;
            Guid riid = new Guid("43826D1E-E718-42EE-BC55-A1E261C37BFE");
            if (SHCreateItemFromParsingName(initialPath, IntPtr.Zero, riid, out folderItem) == 0) {
                dialog.SetFolder(folderItem);
            }
        }

        uint cookie = 0;
        var handler = new DialogEventHandler(dialog, iconPath);
        try {
            dialog.Advise(handler, out cookie);
        } catch { }

        int hr = dialog.Show(owner);

        if (cookie != 0) {
            try { dialog.Unadvise(cookie); } catch { }
        }

        if (hr == 0) {
            IShellItem result;
            dialog.GetResult(out result);
            string path;
            result.GetDisplayName(0x80058000, out path); // SIGDN_FILESYSPATH
            return path;
        }
        return null;
    }
}
"""


def open_native_windows_folder_dialog(initial_dir: str = "", title: str = "Select the folder that holds the episodes") -> Optional[str]:
    """
    Open modern native Windows File Explorer folder picker safely using PowerShell -STA -EncodedCommand.
    Uses modern Vista/Win10/Win11 IFileOpenDialog with full File Explorer GUI (navigation pane, address bar, drives),
    Per-Monitor V2 High DPI crisp font rendering, and SN Tool official logo icon.
    Guaranteed: NEVER calls sys.executable, avoiding PyInstaller child restarts and taskkill issues.
    """
    if not initial_dir or not os.path.exists(initial_dir):
        initial_dir = "D:/" if os.path.exists("D:/") else "C:/"
    init_dir_esc = str(Path(initial_dir).resolve()).replace("'", "''")
    title_esc = str(title).replace("'", "''")
    icon_esc = str(APP_ICON_PATH).replace("'", "''")

    ps_code = f"""
try {{
    Add-Type -TypeDefinition @'
{MODERN_FOLDER_PICKER_CS}
'@
    [ModernFolderPicker]::EnableHighDpi()
    $owner = [ModernFolderPicker]::GetForegroundWindow()
    $res = [ModernFolderPicker]::ShowDialog('{init_dir_esc}', '{title_esc}', '{icon_esc}', $owner)
    if ($res) {{
        [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
        Write-Output ("RESULT:" + $res)
    }} else {{
        Write-Output "CANCELLED"
    }}
    exit 0
}} catch {{
    # Fallback only if COM compilation fails completely
    Add-Type -AssemblyName System.Windows.Forms
    $f = New-Object System.Windows.Forms.OpenFileDialog
    $f.Title = '{title_esc}'
    $f.ValidateNames = $false
    $f.CheckFileExists = $false
    $f.CheckPathExists = $true
    $f.FileName = "Select Folder Here"
    $initDir = '{init_dir_esc}'
    if (Test-Path $initDir) {{ $f.InitialDirectory = $initDir }}
    $res = $f.ShowDialog()
    if ($res -eq [System.Windows.Forms.DialogResult]::OK) {{
        $folder = [System.IO.Path]::GetDirectoryName($f.FileName)
        [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
        Write-Output ("RESULT:" + $folder)
    }} else {{
        Write-Output "CANCELLED"
    }}
    exit 0
}}
"""
    try:
        import base64
        encoded = base64.b64encode(ps_code.encode("utf-16le")).decode("ascii")
        proc = subprocess.run(
            ["powershell.exe", "-STA", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=300,
            **get_silent_kwargs()
        )
        for line in proc.stdout.splitlines():
            line = line.strip()
            if line.startswith("RESULT:"):
                chosen = line[7:].strip().replace("\\", "/")
                if os.path.exists(chosen):
                    return chosen
    except Exception as e:
        print(f"Native folder dialog note: {e}")
    return None


def open_native_windows_files_dialog(initial_dir: str = "", title: str = "Select the video files for the drama series") -> List[str]:
    """
    Open native Windows multi-file picker safely using PowerShell -STA -EncodedCommand with High DPI support.
    Guaranteed safe across all Windows environments without invoking sys.executable.
    """
    if not initial_dir or not os.path.exists(initial_dir):
        initial_dir = "D:/" if os.path.exists("D:/") else "C:/"
    init_dir_esc = str(Path(initial_dir).resolve()).replace("'", "''")
    title_esc = str(title).replace("'", "''")

    ps_code = f"""
Add-Type -AssemblyName System.Windows.Forms
try {{
    Add-Type -TypeDefinition @'
{MODERN_FOLDER_PICKER_CS}
'@
    [ModernFolderPicker]::EnableHighDpi()
}} catch {{ }}

$f = New-Object System.Windows.Forms.OpenFileDialog
$f.Title = '{title_esc}'
$f.Filter = 'Video Files (*.mp4;*.mkv;*.mov;*.avi;*.webm;*.flv;*.ts;*.m4v)|*.mp4;*.mkv;*.mov;*.avi;*.webm;*.flv;*.ts;*.m4v|All Files (*.*)|*.*'
$f.Multiselect = $true
$initDir = '{init_dir_esc}'
if (Test-Path $initDir) {{
    $f.InitialDirectory = $initDir
}}
$res = $f.ShowDialog()
if ($res -eq [System.Windows.Forms.DialogResult]::OK) {{
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $json = ConvertTo-Json -Compress @($f.FileNames)
    Write-Output ("RESULT:" + $json)
}} else {{
    Write-Output "CANCELLED"
}}
$f.Dispose()
exit 0
"""
    try:
        import base64
        encoded = base64.b64encode(ps_code.encode("utf-16le")).decode("ascii")
        proc = subprocess.run(
            ["powershell.exe", "-STA", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=300,
            **get_silent_kwargs()
        )
        for line in proc.stdout.splitlines():
            line = line.strip()
            if line.startswith("RESULT:"):
                raw_json = line[7:].strip()
                parsed = json.loads(raw_json)
                files = [parsed] if isinstance(parsed, str) else list(parsed)
                return [f.replace("\\", "/") for f in files if os.path.exists(f)]
    except Exception as e:
        print(f"Native file dialog note: {e}")
    return []


@app.route("/api/system/select-folder", methods=["POST", "GET"])
@app.route("/api/downloader/select-folder", methods=["POST", "GET"])
def system_select_folder_endpoint():
    """Pop native Windows folder picker dialog and return selected path."""
    data = {}
    if request.is_json:
        data = request.get_json(silent=True) or {}
    initial_dir = data.get("initial_dir", "")
    chosen_path = open_native_windows_folder_dialog(initial_dir, title="Select Download Save Folder")
    if chosen_path:
        return jsonify({"success": True, "path": chosen_path})
    return jsonify({"success": False, "cancelled": True})


@app.route("/api/system/select-media-files", methods=["POST", "GET"])
def system_select_media_files_endpoint():
    """Pop native Windows file picker dialog allowing multi-select of video files."""
    data = {}
    if request.is_json:
        data = request.get_json(silent=True) or {}
    initial_dir = data.get("initial_dir", "")

    chosen_files = open_native_windows_files_dialog(initial_dir, title="Select the video files for the drama series")

    if chosen_files:
        valid_exts = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv", ".ts", ".m4v", ".wmv"}
        meta_files = []
        for fp in chosen_files:
            p = Path(fp)
            if p.exists() and p.is_file() and p.suffix.lower() in valid_exts:
                sz = p.stat().st_size
                meta_files.append({
                    "filepath": str(p.resolve()).replace("\\", "/"),
                    "filename": p.name,
                    "size": sz,
                    "size_mb": f"{sz / (1024 * 1024):.1f}"
                })

        def natural_sort_key(s):
            return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s["filename"])]

        meta_files.sort(key=natural_sort_key)
        return jsonify({"success": True, "files": meta_files, "count": len(meta_files)})

    return jsonify({"success": False, "cancelled": True, "files": []})


@app.route("/api/system/select-media-folder", methods=["POST", "GET"])
def system_select_media_folder_endpoint():
    """Pop native Windows folder picker dialog, scanning and naturally sorting all drama episodes."""
    data = {}
    if request.is_json:
        data = request.get_json(silent=True) or {}
    initial_dir = data.get("initial_dir", "")

    chosen_folder = open_native_windows_folder_dialog(initial_dir, title="Select the folder that holds the episodes")

    if not chosen_folder or not os.path.exists(chosen_folder):
        return jsonify({"success": False, "cancelled": True, "files": []})

    folder_p = Path(chosen_folder)
    valid_exts = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv", ".ts", ".m4v", ".wmv"}

    found_paths = []
    for item in folder_p.iterdir():
        if item.is_file() and item.suffix.lower() in valid_exts:
            found_paths.append(item)
        elif item.is_dir():
            for sub in item.iterdir():
                if sub.is_file() and sub.suffix.lower() in valid_exts:
                    found_paths.append(sub)

    meta_files = []
    for p in found_paths:
        sz = p.stat().st_size
        meta_files.append({
            "filepath": str(p.resolve()).replace("\\", "/"),
            "filename": p.name,
            "size": sz,
            "size_mb": f"{sz / (1024 * 1024):.1f}"
        })

    def natural_sort_key(s):
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s["filename"])]

    meta_files.sort(key=natural_sort_key)

    series_title = folder_p.name
    return jsonify({
        "success": True,
        "folder": str(folder_p).replace("\\", "/"),
        "series_title": series_title,
        "files": meta_files,
        "count": len(meta_files)
    })


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
    voice_override = request.form.get("voice_override")
    aspect_ratio = request.form.get("aspect_ratio", "16:9")
    cfg = load_stored_story_config()
    burn_sub_default = "true" if cfg.get("subtitle_mode", "none") == "burn" else "false"
    burn_subtitles = request.form.get("burn_subtitles", burn_sub_default).lower() in ("true", "1", "yes")
    
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
            original_filename = data.get("filename") or Path(saved_video_path).name
            mode = data.get("drama_mode", mode)
            source_lang = data.get("source_lang", source_lang)
            voice_override = data.get("voice_override", voice_override)
            aspect_ratio = data.get("aspect_ratio", aspect_ratio)
            if "burn_subtitles" in data:
                val = data["burn_subtitles"]
                burn_subtitles = val if isinstance(val, bool) else str(val).lower() in ("true", "1", "yes")
    elif request.form.get("filepath"):
        saved_video_path = request.form.get("filepath")
        original_filename = request.form.get("filename") or Path(saved_video_path).name

    if not voice_override or voice_override in ("auto", "", None):
        cfg = load_stored_story_config()
        if cfg.get("auto_multi_voice") is not False or cfg.get("khmer_voice") == "multi":
            voice_override = "multi"
        else:
            voice_override = cfg.get("khmer_voice", "multi")

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
        def _prog_cb(pct: int, km: str, en: str, dialogues: list = None):
            if t_id in video_auto_tasks:
                video_auto_tasks[t_id]["progress"] = pct
                video_auto_tasks[t_id]["step_km"] = km
                video_auto_tasks[t_id]["step_en"] = en
                if dialogues is not None:
                    video_auto_tasks[t_id]["dialogues"] = dialogues

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
                if res_proj and res_proj.get("dialogues"):
                    video_auto_tasks[t_id]["dialogues"] = res_proj.get("dialogues")
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

    dialogues = task.get("dialogues")
    if not dialogues and task.get("project"):
        dialogues = task["project"].get("dialogues")

    resp = {
        "success": True,
        "task_id": task["task_id"],
        "filename": task.get("filename"),
        "status": task.get("status"),
        "progress": task.get("progress", 0),
        "step_km": task.get("step_km", ""),
        "step_en": task.get("step_en", ""),
        "error": task.get("error"),
        "dialogues": dialogues or []
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


@app.route("/api/projects/merge-episodes", methods=["POST"])
def merge_episodes_endpoint():
    """Merge multiple dubbed episode MP4 files into a single full movie video."""
    data = request.get_json(force=True) or {}
    video_paths = data.get("video_paths", [])
    series_title = data.get("series_title", "Drama_Series")

    clean_title = re.sub(r'[^\w\-_.]', '_', str(series_title)).strip('_')
    if not clean_title:
        clean_title = "Drama_Series"

    output_filename = f"Dubbed_{clean_title}_Full_Movie.mp4"
    out_file = Path("data/exports") / output_filename

    if not video_paths:
        return jsonify({"success": False, "error": "No video paths provided"}), 400

    resolved_paths = []
    for vp in video_paths:
        p = Path(vp)
        if p.exists():
            resolved_paths.append(str(p.resolve()))
            continue
        p_exports = Path("data/exports") / p.name
        if p_exports.exists():
            resolved_paths.append(str(p_exports.resolve()))
            continue
        p_base = (BASE_DIR / vp).resolve()
        if p_base.exists():
            resolved_paths.append(str(p_base))
            continue

    if not resolved_paths:
        return jsonify({"success": False, "error": "No existing episode files found to merge"}), 404

    try:
        from video_processor import merge_videos
        final_path = merge_videos(resolved_paths, str(out_file))
        return jsonify({
            "success": True,
            "merged_path": str(final_path),
            "merged_filename": output_filename,
            "video_url": f"/media/data/exports/{output_filename}"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/media/<path:filename>")
def serve_media(filename):
    file_path = Path(filename)
    if not file_path.exists():
        return jsonify({"error": "Media file not found"}), 404
        
    return send_file(str(file_path.resolve()), conditional=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
