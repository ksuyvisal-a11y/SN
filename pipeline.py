"""
Unified Drama Voice Translation & Facebook Movie Recap Pipeline Manager (V2.0 Pro)
"""
import os
import json
import uuid
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional

from tts_engine import batch_synthesize, synthesize_khmer_speech, get_available_voices
from translator import DramaTranslator, parse_srt_content, format_srt_content
from audio_processor import (
    extract_audio_from_video,
    mix_dubbed_audio,
    create_waveform_data,
    get_media_duration
)
from tts_engine import batch_synthesize

def safe_float(val: Any, default: float = 0.02) -> float:
    """Safely convert value to float with reliable fallback against empty strings and None."""
    try:
        if val is None or str(val).strip() == "":
            return default
        return float(val)
    except (ValueError, TypeError):
        return default

from video_processor import render_dubbed_video, generate_sample_drama_video
from vocal_remover import separate_vocals_and_bgm
from stt_engine import SpeechToTextEngine
from recap_engine import RecapEngine, VIRAL_KHMER_HOOKS
from downloader import download_video_from_url

DATA_DIR = Path("data/projects")
DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_DRAMAS = {
    "chinese_romance": {
        "title": "រឿងភាគចិន៖ និស្ស័យស្នេហ៍លោកម្ចាស់ (Chinese Drama Sample)",
        "source_lang": "zh",
        "mode": "drama_dubbing",
        "description": "ឈុតឆាកសន្ទនារវាងតួប្រុស (ពិសិដ្ឋ) និងតួស្រី (ស្រីមុំ) ក្នុងរឿងភាគបុរាណចិន",
        "dialogues": [
            {
                "id": 1,
                "start": 0.5,
                "end": 3.8,
                "speaker": "តួប្រុស (Male Lead)",
                "text_original": "你终于来了，我已经在这里等了你三天三夜。",
                "text_km": "ទីបំផុតអូនបានមកដល់ហើយ បងបានរង់ចាំអូននៅទីនេះអស់រយៈពេលបីថ្ងៃបីយប់ហើយ។",
                "voice": "piseth",
                "rate_percent": 0,
                "pitch_hz": 0
            },
            {
                "id": 2,
                "start": 4.2,
                "end": 7.5,
                "speaker": "តួស្រី (Female Lead)",
                "text_original": "对不起，路上遇到了皇宫的追兵，我好不容易才逃出来的。",
                "text_km": "អូនសុំទោស តាមផ្លូវអូនបានជួបទាហានតាមចាប់ ពិបាកណាស់ទម្រាំតែអូនអាចរត់គេចខ្លួនបាន។",
                "voice": "sreymom",
                "rate_percent": 0,
                "pitch_hz": 0
            },
            {
                "id": 3,
                "start": 8.0,
                "end": 11.2,
                "speaker": "តួប្រុស (Male Lead)",
                "text_original": "别怕，只要有我在，没有任何人能够伤害你！",
                "text_km": "កុំខ្លាចអី ដរាបណាមានបងនៅក្បែរ គ្មានអ្នកណាអាចមកធ្វើបាបអូនបានឡើយ!",
                "voice": "piseth",
                "rate_percent": 0,
                "pitch_hz": 0
            },
            {
                "id": 4,
                "start": 11.8,
                "end": 15.0,
                "speaker": "តួស្រី (Female Lead)",
                "text_original": "我相信你，从此以后无论生死我都跟随你。",
                "text_km": "អូនជឿជាក់លើបង ចាប់ពីពេលនេះទៅ ទោះស្លាប់រស់ក៏អូននៅតែដើរតាមបងជានិច្ច។",
                "voice": "sreymom",
                "rate_percent": 0,
                "pitch_hz": 0
            }
        ]
    },
    "korean_action": {
        "title": "រឿងភាគកូរ៉េ៖ បេសកកម្មសម្ងាត់ (Korean Action Drama Sample)",
        "source_lang": "ko",
        "mode": "drama_dubbing",
        "description": "ឈុតឆាកស៊ើបអង្កេត និងប្រឈមមុខដាក់គ្នារវាងភ្នាក់ងារសម្ងាត់",
        "dialogues": [
            {
                "id": 1,
                "start": 0.5,
                "end": 3.6,
                "speaker": "ប្រធានក្រុម (Team Leader)",
                "text_original": "지금 즉시 작전을 시작한다. 모든 대원은 위치로 이동하라.",
                "text_km": "ចាប់ផ្តើមប្រតិបត្តិការភ្លាម! សមាជិកទាំងអស់ត្រូវចូលទៅកាន់ទីតាំងជាបន្ទាន់។",
                "voice": "piseth",
                "rate_percent": 5,
                "pitch_hz": 0
            },
            {
                "id": 2,
                "start": 4.0,
                "end": 7.2,
                "speaker": "ភ្នាក់ងារស្រី (Female Agent)",
                "text_original": "타겟이 건물 안으로 진입했습니다. 제가 먼저 추적하겠습니다.",
                "text_km": "គោលដៅបានដើរចូលទៅក្នុងអគារហើយ ខ្ញុំនឹងតាមដានពីក្រោយជាមុនសិន។",
                "voice": "sreymom",
                "rate_percent": 0,
                "pitch_hz": 0
            },
            {
                "id": 3,
                "start": 7.8,
                "end": 11.0,
                "speaker": "ប្រធានក្រុម (Team Leader)",
                "text_original": "조심해, 함정일 수도 있어. 지원팀이 곧 도착한다!",
                "text_km": "ប្រយ័ត្នខ្លួនណា! អាចជាអន្ទាក់ ក្រុមជំនួយនឹងទៅដល់ក្នុងពេលបន្តិចទៀតនេះ!",
                "voice": "piseth",
                "rate_percent": 0,
                "pitch_hz": 0
            }
        ]
    },
    "facebook_recap": {
        "title": "សម្រាយរឿង Facebook/TikTok៖ កំពូលអ្នកក្លាហាន (FB Movie Recap Style)",
        "source_lang": "en",
        "mode": "movie_recap",
        "description": "ទម្រង់សម្រាយសាច់រឿងទាក់ទាញបែប Facebook និង TikTok ដោយប្រើសំឡេងពិសិដ្ឋ និងស្រីមុំ",
        "dialogues": [
            {
                "id": 1,
                "start": 0.5,
                "end": 4.2,
                "speaker": "អ្នកសម្រាយ (Recap Host - Piseth)",
                "text_original": "This man thought he was just an ordinary worker, but he didn't know he was actually the billionaire's heir.",
                "text_km": "បុរសម្នាក់នេះគិតថាខ្លួនឯងគ្រាន់តែជាកម្មករធម្មតា ប៉ុន្តែគាត់មិនដឹងឡើយថា តាមពិតគាត់គឺជាអ្នកស្នងមរតកត្រកូលមហាសេដ្ឋី។",
                "voice": "piseth",
                "rate_percent": 5,
                "pitch_hz": 0
            },
            {
                "id": 2,
                "start": 4.8,
                "end": 8.5,
                "speaker": "អ្នករៀបរាប់ (Co-Host - Sreymom)",
                "text_original": "At that exact moment, a luxury car pulled up and changed his entire life forever.",
                "text_km": "ស្រាប់តែនៅពេលនោះ ឡានទំនើបមួយគ្រឿងបានមកឈប់នៅពីមុខគាត់ ហើយបានផ្លាស់ប្តូរជីវិតរបស់គាត់ជារៀងរហូត។",
                "voice": "sreymom",
                "rate_percent": 0,
                "pitch_hz": 0
            },
            {
                "id": 3,
                "start": 9.0,
                "end": 13.5,
                "speaker": "អ្នកសម្រាយ (Recap Host - Piseth)",
                "text_original": "What do you think he will do next? Don't forget to like and follow for episode 2!",
                "text_km": "តើអ្នកទាំងអស់គ្នាគិតថាគាត់នឹងធ្វើអ្វីបន្តទៀត? កុំភ្លេចចុច Like និង Follow ដើម្បីរង់ចាំទស្សនាភាគទីពីរទាំងអស់គ្នា!",
                "voice": "piseth",
                "rate_percent": 0,
                "pitch_hz": 0
            }
        ]
    }
}


class ProjectManager:
    def __init__(self):
        self.translator = DramaTranslator()
        cfg_model = "base"
        try:
            cfg_file = Path("data/story_config.json")
            if cfg_file.exists():
                with open(cfg_file, "r", encoding="utf-8") as f:
                    cfg_model = json.load(f).get("whisper_model", "base")
        except Exception:
            pass
        self.stt_engine = SpeechToTextEngine(model_size=cfg_model if cfg_model in ("tiny", "base", "small", "medium") else "base")

    def get_project_file(self, project_id: str) -> Path:
        return DATA_DIR / f"{project_id}.json"

    def create_project(self, title: str = "New Drama Dubbing Project", mode: str = "drama_dubbing") -> Dict[str, Any]:
        project_id = str(uuid.uuid4())[:8]
        proj_dir = Path(f"data/projects/{project_id}")
        proj_dir.mkdir(parents=True, exist_ok=True)
        
        # Load default ducking from story_config.json
        cfg_duck = 0.15
        try:
            cfg_p = Path("data/story_config.json")
            if cfg_p.exists():
                with open(cfg_p, "r", encoding="utf-8") as f:
                    cfg_duck = safe_float(json.load(f).get("ducking_volume"), 0.15)
        except Exception:
            cfg_duck = 0.15

        project = {
            "id": project_id,
            "title": title,
            "mode": mode,
            "source_lang": "auto",
            "video_file": None,
            "original_audio_file": None,
            "isolated_bgm_file": None,
            "mixed_audio_file": None,
            "output_video_file": None,
            "duration": 0.0,
            "ducking_factor": cfg_duck,
            "burn_subtitles": False,
            "aspect_ratio": "16:9",  # 16:9 or 9:16
            "watermark_text": "",
            "dialogues": [],
            "waveform": []
        }
        self.save_project(project)
        return project

    def save_project(self, project: Dict[str, Any]) -> None:
        p_file = self.get_project_file(project["id"])
        with open(p_file, "w", encoding="utf-8") as f:
            json.dump(project, f, ensure_ascii=False, indent=2)

    def load_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        p_file = self.get_project_file(project_id)
        if p_file.exists():
            with open(p_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def list_projects(self) -> List[Dict[str, Any]]:
        projects = []
        for p_file in DATA_DIR.glob("*.json"):
            try:
                with open(p_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    projects.append({
                        "id": data.get("id"),
                        "title": data.get("title"),
                        "mode": data.get("mode"),
                        "dialogues_count": len(data.get("dialogues", [])),
                        "duration": data.get("duration", 0)
                    })
            except Exception:
                pass
        return projects

    def load_sample(self, sample_key: str) -> Dict[str, Any]:
        sample_data = SAMPLE_DRAMAS.get(sample_key, SAMPLE_DRAMAS["chinese_romance"])
        project = self.create_project(title=sample_data["title"], mode=sample_data["mode"])
        project["source_lang"] = sample_data["source_lang"]
        project["dialogues"] = sample_data["dialogues"]
        
        proj_dir = Path(f"data/projects/{project['id']}")
        video_sample_path = proj_dir / "sample_video.mp4"
        audio_sample_path = proj_dir / "original_audio.wav"
        
        try:
            generate_sample_drama_video(str(video_sample_path), duration_sec=16)
            extract_audio_from_video(str(video_sample_path), str(audio_sample_path))
            project["video_file"] = str(video_sample_path)
            project["original_audio_file"] = str(audio_sample_path)
            project["duration"] = 16.0
            project["waveform"] = create_waveform_data(str(audio_sample_path))
        except Exception as e:
            print(f"Sample video creation note: {e}")

        self.save_project(project)
        return project

    def auto_transcribe_project(self, project_id: str) -> Dict[str, Any]:
        """Transcribe audio from project media file using AI Speech-to-Text on isolated vocals."""
        project = self.load_project(project_id)
        if not project or not project.get("original_audio_file"):
            raise ValueError("No audio file found to transcribe")

        audio_path = project.get("isolated_vocals_file")
        if not audio_path or not Path(audio_path).exists() or Path(audio_path).stat().st_size < 1000:
            audio_path = project["original_audio_file"]

        dialogues = self.stt_engine.transcribe_audio(
            audio_path=str(audio_path),
            source_lang=project.get("source_lang", "auto")
        )
        project["dialogues"] = dialogues
        self.save_project(project)
        return project

    def separate_project_vocals(self, project_id: str) -> Dict[str, Any]:
        """Separate dialogue vocals from background music/effects."""
        project = self.load_project(project_id)
        if not project or not project.get("original_audio_file"):
            raise ValueError("No audio found for vocal separation")

        proj_dir = Path(f"data/projects/{project_id}")
        bgm_path, voc_path = separate_vocals_and_bgm(project["original_audio_file"], output_dir=str(proj_dir))
        project["isolated_bgm_file"] = bgm_path
        if voc_path and Path(voc_path).exists():
            project["isolated_vocals_file"] = str(voc_path)
        self.save_project(project)
        return project

    async def translate_project(
        self,
        project_id: str,
        mode: Optional[str] = None,
        source_lang: Optional[str] = None,
        voice_override: Optional[str] = None
    ) -> Dict[str, Any]:
        project = self.load_project(project_id)
        if not project:
            raise ValueError("Project not found")

        mode = mode or project.get("mode", "drama_dubbing")
        source_lang = source_lang or project.get("source_lang", "auto")
        
        if not voice_override or voice_override in (None, "", "auto"):
            cfg = {}
            try:
                cfg_p = Path("data/story_config.json")
                if cfg_p.exists():
                    with open(cfg_p, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
            except Exception:
                pass
            if cfg.get("auto_multi_voice") is not False or cfg.get("khmer_voice") == "multi":
                v_override = "multi"
            else:
                v_override = cfg.get("khmer_voice", "multi")
        else:
            v_override = voice_override

        # Ensure dialogues have acoustic diarization if in multi-voice mode
        if v_override in ("multi", "auto_multi"):
            target_audio = project.get("isolated_vocals_file") or project.get("audio_file")
            if target_audio and Path(target_audio).exists():
                try:
                    from stt_engine import analyze_segment_acoustics
                    for d in project.get("dialogues", []):
                        spk_low = str(d.get("speaker", "")).lower()
                        if not d.get("detected_role") or "solo" in spk_low:
                            s_time = float(d.get("start", 0.0))
                            e_time = float(d.get("end", s_time + 1.0))
                            ac = analyze_segment_acoustics(str(target_audio), s_time, e_time)
                            if ac.get("role") in ("female", "male"):
                                d["detected_role"] = ac["role"]
                                d["voice"] = ac["voice"]
                except Exception as e:
                    print(f"Acoustic re-diarization notice: {e}")

        translated_dialogues = await self.translator.translate_dialogues(
            dialogues=project.get("dialogues", []),
            mode=mode,
            source_lang=source_lang,
            target_voice_override=v_override,
            drama_title=project.get("title")
        )

        if v_override not in ("multi", "auto_multi"):
            chosen_v = "sreymom" if v_override == "sreymom" else "piseth"
            v_desc = "ស្រីមុំ (Sreymom Solo)" if chosen_v == "sreymom" else "ពិសិដ្ឋ (Piseth Solo)"
            for d in translated_dialogues:
                d["voice"] = chosen_v
                d["pitch_hz"] = 0
                d["rate_percent"] = 0
                d["speaker"] = v_desc

        project["dialogues"] = translated_dialogues
        project["mode"] = mode
        project["source_lang"] = source_lang
        self.save_project(project)
        return project

    async def generate_project_audio(self, project_id: str) -> Dict[str, Any]:
        project = self.load_project(project_id)
        if not project:
            raise ValueError("Project not found")

        proj_dir = Path(f"data/projects/{project['id']}")
        voice_out_dir = proj_dir / "voices"
        voice_out_dir.mkdir(parents=True, exist_ok=True)

        processed_dialogues = await batch_synthesize(
            dialogue_items=project.get("dialogues", []),
            output_dir=str(voice_out_dir)
        )
        project["dialogues"] = processed_dialogues

        # Automatically separate vocals if not already done
        # Automatically separate vocals if not already done
        if (not project.get("isolated_bgm_file") or not Path(str(project.get("isolated_bgm_file"))).exists()) and project.get("original_audio_file"):
            try:
                bgm_path, voc_path = separate_vocals_and_bgm(project["original_audio_file"], output_dir=str(proj_dir))
                project["isolated_bgm_file"] = bgm_path
            except Exception as e:
                print(f"Auto separation note: {e}")

        cfg_data = {}
        try:
            cfg_p = Path("data/story_config.json")
            if cfg_p.exists():
                with open(cfg_p, "r", encoding="utf-8") as f:
                    cfg_data = json.load(f)
        except Exception:
            pass

        bgm_track = project.get("isolated_bgm_file") or project.get("original_audio_file")
        if not Path(str(bgm_track)).exists():
            bgm_track = project.get("original_audio_file")

        mixed_audio_path = proj_dir / "mixed_dubbed_audio.mp3"
        duck_val = safe_float(cfg_data.get("ducking_volume"), safe_float(project.get("ducking_factor"), 0.15))
        dub_mode = cfg_data.get("dubbing_mode", "smart_bgm")
        speech_boost = safe_float(cfg_data.get("speech_boost_db"), 2.5)

        mix_dubbed_audio(
            original_audio_path=bgm_track,
            dialogue_items=processed_dialogues,
            output_mixed_path=str(mixed_audio_path),
            total_duration_sec=project.get("duration", 0),
            ducking_volume_factor=duck_val,
            speech_volume_boost_db=speech_boost,
            dubbing_mode=dub_mode
        )

        project["mixed_audio_file"] = str(mixed_audio_path)
        project["waveform"] = create_waveform_data(str(mixed_audio_path))
        self.save_project(project)
        return project

    def render_project_video_final(
        self,
        project_id: str,
        burn_subtitles: bool = False,
        aspect_ratio: str = "16:9",
        watermark_text: Optional[str] = None
    ) -> Dict[str, Any]:
        project = self.load_project(project_id)
        if not project:
            raise ValueError("Project not found")

        video_in = project.get("video_file")
        mixed_audio = project.get("mixed_audio_file")
        if not video_in or not Path(video_in).exists():
            raise ValueError("No video file found in project to render.")
        if not mixed_audio or not Path(mixed_audio).exists():
            raise ValueError("No mixed audio found. Please generate speech audio first.")

        proj_dir = Path(f"data/projects/{project['id']}")
        output_video_path = proj_dir / "final_dubbed_video.mp4"

        render_dubbed_video(
            original_video_path=video_in,
            mixed_audio_path=mixed_audio,
            output_video_path=str(output_video_path),
            dialogues=project.get("dialogues", []),
            burn_subtitles=burn_subtitles,
            aspect_ratio=aspect_ratio,
            watermark_text=watermark_text,
            temp_dir=str(proj_dir / "temp")
        )

        project["output_video_file"] = str(output_video_path)
        project["burn_subtitles"] = burn_subtitles
        project["aspect_ratio"] = aspect_ratio
        project["watermark_text"] = watermark_text or ""

        # Mirror cleanly to drama unified folder and generate .srt
        try:
            import shutil
            from translator import format_srt_content
            from batch_engine import resolve_drama_export_directories
            clean_title = project.get("title") or Path(video_in).stem
            dest_dirs = resolve_drama_export_directories(video_in, clean_title)
            out_stem = f"Dubbed_{Path(video_in).stem}"
            for d in dest_dirs:
                shutil.copy2(str(output_video_path), str(d / f"{out_stem}.mp4"))
                if project.get("dialogues"):
                    srt_txt = format_srt_content(project["dialogues"], use_km=True)
                    (d / f"{out_stem}.srt").write_text(srt_txt, encoding="utf-8")
        except Exception as e:
            print(f"Unified drama folder export note: {e}")

        self.save_project(project)
        return project

    async def process_video_pipeline(
        self,
        video_path: str,
        title: Optional[str] = None,
        mode: str = "drama_dubbing",
        source_lang: str = "auto",
        voice_override: Optional[str] = None,
        aspect_ratio: str = "16:9",
        burn_subtitles: bool = False,
        progress_callback = None
    ) -> Dict[str, Any]:
        """
        Complete 1-Click Automated Video Dubbing Pipeline:
        1. Extract Audio & Waveform (15%)
        2. Speech-to-Text via Faster-Whisper (35%)
        3. Translate Script to Natural Khmer Drama Dubbing (55%)
        4. Synthesize Khmer Voices with Piseth & Sreymom Neural TTS (75%)
        5. Smart Audio Ducking & BGM Mixing (85%)
        6. Render Final Master MP4 & Export (95%)
        """
        def update_prog(pct: int, msg_km: str, msg_en: str, dialogues = None):
            if progress_callback:
                try:
                    import inspect
                    sig = inspect.signature(progress_callback)
                    if len(sig.parameters) >= 4:
                        progress_callback(pct, msg_km, msg_en, dialogues)
                    else:
                        progress_callback(pct, msg_km, msg_en)
                except Exception:
                    try:
                        progress_callback(pct, msg_km, msg_en)
                    except Exception:
                        pass

        src_file = Path(video_path)
        if not src_file.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        proj_title = title or f"Dubbed_{src_file.stem}"
        project = self.create_project(title=proj_title, mode=mode)
        proj_id = project["id"]
        proj_dir = Path(f"data/projects/{proj_id}")
        proj_dir.mkdir(parents=True, exist_ok=True)

        # 1. Video & Audio Preparation (Direct zero-copy referencing for ultra-fast processing)
        update_prog(12, "១/៧ កំពុងទាញយកសំឡេងពីវីដេអូ...", "Extracting audio from video...")
        dest_video = src_file
        audio_dest = proj_dir / "original_audio.wav"
        extract_audio_from_video(str(dest_video), str(audio_dest))
        
        project["video_file"] = str(dest_video)
        project["original_audio_file"] = str(audio_dest)
        project["duration"] = get_media_duration(str(dest_video))
        project["waveform"] = create_waveform_data(str(audio_dest))
        project["aspect_ratio"] = aspect_ratio
        project["burn_subtitles"] = burn_subtitles
        self.save_project(project)

        # 2. Vocal Separation (Isolate BGM, Eliminate Chinese Vocals)
        update_prog(28, "២/៧ កំពុងច្រោះសំឡេងចិនដើមចេញពីភ្លេង (Vocal Isolation)...", "Separating Chinese vocals from BGM...")
        voc_file = None
        try:
            bgm_file, voc_file = separate_vocals_and_bgm(str(audio_dest), output_dir=str(proj_dir))
            project["isolated_bgm_file"] = bgm_file
            if voc_file and Path(voc_file).exists():
                project["isolated_vocals_file"] = str(voc_file)
        except Exception as e:
            print(f"Vocal separation warning: {e}")
            project["isolated_bgm_file"] = str(audio_dest)
        self.save_project(project)

        # Resolve Voice Mode (Piseth Solo, Sreymom Solo, or Dual Multi-Voice)
        cfg_data = {}
        try:
            cfg_p = Path("data/story_config.json")
            if cfg_p.exists():
                with open(cfg_p, "r", encoding="utf-8") as f:
                    cfg_data = json.load(f)
        except Exception:
            pass

        if not voice_override or voice_override in (None, "", "auto"):
            if cfg_data.get("auto_multi_voice") is not False or cfg_data.get("khmer_voice") == "multi":
                voice_override = "multi"
            else:
                voice_override = cfg_data.get("khmer_voice", "multi")

        v_override = str(voice_override).lower().strip()
        is_multi = v_override in ("multi", "auto_multi")
        if is_multi:
            voice_label = "ពិសិដ្ឋ & ស្រីមុំ (Dual Voice)"
        elif v_override == "sreymom":
            voice_label = "ស្រីមុំ (Sreymom Solo)"
        else:
            voice_label = "ពិសិដ្ឋ (Piseth Solo)"

        # 3. Speech-to-Text (Auto Transcribe via Faster-Whisper with word-level timestamps)
        update_prog(45, f"៣/៧ AI កំពុងស្តាប់ និងចាប់សំឡេងដើម ({voice_label})...", "Transcribing speech...")
        # Use isolated vocals (clean without BGM) for ultra-accurate transcription & F0 pitch diarization
        stt_target_audio = project.get("isolated_vocals_file") or str(audio_dest)
        if not Path(stt_target_audio).exists() or Path(stt_target_audio).stat().st_size < 1000:
            stt_target_audio = str(audio_dest)
        try:
            dialogues = self.stt_engine.transcribe_audio(
                audio_path=stt_target_audio,
                source_lang=source_lang,
                voice_override=v_override,
                progress_callback=update_prog,
                video_path=str(dest_video)
            )
        except Exception as e:
            print(f"STT Exception: {e}")
            dialogues = []

        # Robust Fallback: If isolated vocals produced 0 dialogues or failed, retry directly on original audio!
        if not dialogues and str(audio_dest) != str(stt_target_audio) and Path(audio_dest).exists():
            print("Notice: Isolated vocals yielded 0 dialogues, falling back to original audio for STT...")
            update_prog(48, f"៣/៧ កំពុងស្កេនសំឡេងដើមឡើងវិញ ({voice_label})...", "Retrying transcription on original audio...")
            try:
                dialogues = self.stt_engine.transcribe_audio(
                    audio_path=str(audio_dest),
                    source_lang=source_lang,
                    voice_override=v_override,
                    progress_callback=update_prog
                )
            except Exception as e2:
                print(f"STT Fallback Exception: {e2}")

        if not dialogues:
            print("Warning: No speech segments were detected by the STT engine for this audio.")

        project["dialogues"] = dialogues
        self.save_project(project)

        # 4. Translate to Khmer Drama Dialogue (Strictly honors Piseth, Sreymom, or Dual Voice)
        update_prog(62, f"៤/៧ AI កំពុងបកប្រែជាភាសាខ្មែរ {voice_label} (Story Bible)...", f"Translating script to {voice_label}...")
        translated = await self.translator.translate_dialogues(
            dialogues=dialogues,
            mode=mode,
            source_lang=source_lang,
            target_voice_override=v_override,
            drama_title=proj_title
        )
        if not is_multi:
            chosen_v = "sreymom" if v_override == "sreymom" else "piseth"
            v_desc = "ស្រីមុំ (Sreymom Solo)" if chosen_v == "sreymom" else "ពិសិដ្ឋ (Piseth Solo)"
            for d in translated:
                d["voice"] = chosen_v
                d["pitch_hz"] = 0
                d["rate_percent"] = 0
                d["speaker"] = v_desc

        project["dialogues"] = translated
        self.save_project(project)
        update_prog(68, f"៤/៧ បកប្រែបានជោគជ័យ! កំពុងត្រៀមបញ្ចូលសំឡេង {voice_label}...", "Translation completed! Preparing voice synthesis...", dialogues=translated)

        # 5. Neural Khmer Voice Synthesis
        update_prog(76, f"៥/៧ កំពុងបញ្ចូលសំឡេងខ្មែរ {voice_label}...", f"Synthesizing Khmer neural speech ({voice_label})...")
        voice_out_dir = proj_dir / "voices"
        voice_out_dir.mkdir(parents=True, exist_ok=True)
        synthesized = await batch_synthesize(
            translated,
            output_dir=str(voice_out_dir),
            default_voice="piseth" if is_multi else v_override
        )
        project["dialogues"] = synthesized
        self.save_project(project)

        # 6. Audio Ducking & Clean BGM Mixing (Zero Vocal Leakage)
        update_prog(88, "៦/៧ កំពុងសម្រួលសំឡេង BGM & សំឡេងខ្មែរ (Zero Vocal Leakage)...", "Mixing dubbed audio with clean BGM...")
        mixed_audio = proj_dir / "mixed_dubbed_audio.mp3"
        bgm_track = project.get("isolated_bgm_file") or str(audio_dest)
        if not Path(bgm_track).exists():
            bgm_track = str(audio_dest)
        duck_val = safe_float(cfg_data.get("ducking_volume"), safe_float(project.get("ducking_factor"), 0.15))
        dub_mode = cfg_data.get("dubbing_mode", "smart_bgm")
        speech_boost = safe_float(cfg_data.get("speech_boost_db"), 2.5)
        mix_dubbed_audio(
            original_audio_path=bgm_track,
            dialogue_items=synthesized,
            output_mixed_path=str(mixed_audio),
            total_duration_sec=project.get("duration", 0),
            ducking_volume_factor=duck_val,
            speech_volume_boost_db=speech_boost,
            dubbing_mode=dub_mode
        )
        project["mixed_audio_file"] = str(mixed_audio)
        project["waveform"] = create_waveform_data(str(mixed_audio))
        self.save_project(project)

        # 7. Render Final Video
        update_prog(95, "៧/៧ កំពុង Render វីដេអូ MP4 ជាសំឡេងខ្មែរ...", "Rendering final dubbed video...")
        rendered_project = self.render_project_video_final(
            project_id=proj_id,
            burn_subtitles=burn_subtitles,
            aspect_ratio=aspect_ratio
        )

        update_prog(100, "🎉 រួចរាល់ ១០០%! វីដេអូសម្រេចបានរក្សាទុក!", "Completed! Video ready.")
        return rendered_project
