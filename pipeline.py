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
from audio_processor import extract_audio_from_video, mix_dubbed_audio, create_waveform_data, get_media_duration
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
        self.stt_engine = SpeechToTextEngine(model_size="tiny")

    def get_project_file(self, project_id: str) -> Path:
        return DATA_DIR / f"{project_id}.json"

    def create_project(self, title: str = "New Drama Dubbing Project", mode: str = "drama_dubbing") -> Dict[str, Any]:
        project_id = str(uuid.uuid4())[:8]
        proj_dir = Path(f"data/projects/{project_id}")
        proj_dir.mkdir(parents=True, exist_ok=True)
        
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
            "ducking_factor": 0.25,
            "burn_subtitles": True,
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
        """Transcribe audio from project media file using AI Speech-to-Text."""
        project = self.load_project(project_id)
        if not project or not project.get("original_audio_file"):
            raise ValueError("No audio file found to transcribe")

        audio_path = project["original_audio_file"]
        dialogues = self.stt_engine.transcribe_audio(
            audio_path=audio_path,
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

        translated_dialogues = await self.translator.translate_dialogues(
            dialogues=project.get("dialogues", []),
            mode=mode,
            source_lang=source_lang,
            target_voice_override=voice_override
        )

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

        # Prefer isolated BGM if separated, otherwise original audio
        bgm_track = project.get("isolated_bgm_file") or project.get("original_audio_file")
        mixed_audio_path = proj_dir / "mixed_dubbed_audio.mp3"

        mix_dubbed_audio(
            original_audio_path=bgm_track,
            dialogue_items=processed_dialogues,
            output_mixed_path=str(mixed_audio_path),
            total_duration_sec=project.get("duration", 0),
            ducking_volume_factor=float(project.get("ducking_factor", 0.25))
        )

        project["mixed_audio_file"] = str(mixed_audio_path)
        project["waveform"] = create_waveform_data(str(mixed_audio_path))
        self.save_project(project)
        return project

    def render_project_video_final(
        self,
        project_id: str,
        burn_subtitles: bool = True,
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
        burn_subtitles: bool = True,
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
        def update_prog(pct: int, msg_km: str, msg_en: str):
            if progress_callback:
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

        # 1. Copy Video & Extract Audio
        update_prog(15, "១/៦ កំពុងទាញយកសំឡេងពីវីដេអូ...", "Extracting audio from video...")
        import shutil
        dest_video = proj_dir / f"source_media{src_file.suffix.lower()}"
        if src_file.resolve() != dest_video.resolve():
            shutil.copy2(str(src_file), str(dest_video))
        
        audio_dest = proj_dir / "original_audio.wav"
        extract_audio_from_video(str(dest_video), str(audio_dest))
        
        project["video_file"] = str(dest_video)
        project["original_audio_file"] = str(audio_dest)
        project["duration"] = get_media_duration(str(dest_video))
        project["waveform"] = create_waveform_data(str(audio_dest))
        project["aspect_ratio"] = aspect_ratio
        project["burn_subtitles"] = burn_subtitles
        self.save_project(project)

        # 2. Speech-to-Text (Auto Transcribe)
        update_prog(35, "២/៦ AI កំពុងស្តាប់ និងចាប់សំឡេងចិន (Faster-Whisper)...", "Transcribing speech...")
        try:
            dialogues = self.stt_engine.transcribe_audio(
                audio_path=str(audio_dest),
                source_lang=source_lang
            )
        except Exception as e:
            print(f"STT Exception: {e}")
            dialogues = []

        if not dialogues:
            # Fallback dialogue if audio had low volume
            dur = project.get("duration") or 5.0
            dialogues = [{
                "id": 1,
                "start": 0.5,
                "end": max(2.5, dur - 0.5),
                "speaker": "តួអង្គ",
                "text": "你好",
                "text_original": "你好"
            }]

        project["dialogues"] = dialogues
        self.save_project(project)

        # 3. Translate to Khmer Drama Dialogue
        update_prog(55, "៣/៦ AI កំពុងបកប្រែជាភាសាខ្មែរ (រឿងភាគ)...", "Translating script to natural Khmer...")
        v_override = None if voice_override in (None, "", "auto") else voice_override
        translated = await self.translator.translate_dialogues(
            dialogues=dialogues,
            mode=mode,
            source_lang=source_lang,
            target_voice_override=v_override
        )
        project["dialogues"] = translated
        self.save_project(project)

        # 4. Neural Khmer Voice Synthesis (Piseth & Sreymom)
        update_prog(75, "៤/៦ កំពុងបញ្ចូលសំឡេងខ្មែរ ពិសិដ្ឋ & ស្រីមុំ...", "Synthesizing Khmer neural speech...")
        voice_out_dir = proj_dir / "voices"
        voice_out_dir.mkdir(parents=True, exist_ok=True)
        synthesized = await batch_synthesize(translated, output_dir=str(voice_out_dir))
        project["dialogues"] = synthesized
        self.save_project(project)

        # 5. Audio Ducking & Mixing
        update_prog(85, "៥/៦ កំពុងសម្រួលសំឡេង BGM & សំឡេងខ្មែរ (Audio Ducking)...", "Mixing dubbed audio with background ducking...")
        mixed_audio = proj_dir / "mixed_dubbed_audio.mp3"
        mix_dubbed_audio(
            original_audio_path=str(audio_dest),
            dialogue_items=synthesized,
            output_mixed_path=str(mixed_audio),
            total_duration_sec=project.get("duration", 0),
            ducking_volume_factor=float(project.get("ducking_factor", 0.25))
        )
        project["mixed_audio_file"] = str(mixed_audio)
        project["waveform"] = create_waveform_data(str(mixed_audio))
        self.save_project(project)

        # 6. Render Final Video
        update_prog(95, "៦/៦ កំពុង Render វីដេអូ MP4 ជាសំឡេងខ្មែរ...", "Rendering final dubbed video...")
        rendered_project = self.render_project_video_final(
            project_id=proj_id,
            burn_subtitles=burn_subtitles,
            aspect_ratio=aspect_ratio
        )

        update_prog(100, "🎉 រួចរាល់ ១០០%! វីដេអូសម្រេចបានរក្សាទុក!", "Completed! Video ready.")
        return rendered_project
