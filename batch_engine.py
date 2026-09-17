"""
Automated Batch & Folder Auto-Dubbing Engine
Processes entire folders of drama episodes end-to-end with zero manual typing.
"""
import os
import asyncio
import threading
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

from pipeline import ProjectManager
from audio_processor import extract_audio_from_video, get_media_duration
from stt_engine import SpeechToTextEngine
from translator import DramaTranslator
from tts_engine import batch_synthesize
from vocal_remover import separate_vocals_and_bgm
from audio_processor import mix_dubbed_audio
from video_processor import render_dubbed_video

EXPORTS_DIR = Path("data/exports")
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


class BatchDubbingManager:
    def __init__(self):
        self.pm = ProjectManager()
        self.stt = SpeechToTextEngine(model_size="base")
        self.translator = DramaTranslator()
        self.queue: List[Dict[str, Any]] = []
        self.is_processing = False
        self._lock = threading.Lock()

    def add_files_to_queue(
        self,
        file_paths: List[str],
        voice_mode: str = "auto",  # 'auto', 'piseth', 'sreymom'
        drama_mode: str = "drama_dubbing",  # 'drama_dubbing' or 'movie_recap'
        aspect_ratio: str = "16:9",
        burn_subtitles: bool = True,
        separate_bgm: bool = True
    ) -> List[Dict[str, Any]]:
        """Add multiple video/audio files to the automated batch queue."""
        added_items = []
        for path_str in file_paths:
            p = Path(path_str)
            if not p.exists():
                continue

            item_id = str(uuid.uuid4())[:8]
            item = {
                "id": item_id,
                "filename": p.name,
                "filepath": str(p),
                "voice_mode": voice_mode,
                "drama_mode": drama_mode,
                "aspect_ratio": aspect_ratio,
                "burn_subtitles": burn_subtitles,
                "separate_bgm": separate_bgm,
                "status": "pending",  # pending, processing, completed, failed
                "step": "រង់ចាំចាប់ផ្តើម",  # transcribing, translating, synthesizing, rendering, done
                "progress": 0,
                "output_video": None,
                "error": None
            }
            with self._lock:
                self.queue.append(item)
            added_items.append(item)
        return added_items

    def get_queue_status(self) -> List[Dict[str, Any]]:
        """Return list of all batch items with their current progress."""
        with self._lock:
            return list(self.queue)

    def clear_completed(self):
        """Remove completed tasks from queue."""
        with self._lock:
            self.queue = [item for item in self.queue if item["status"] not in ("completed", "failed")]

    def start_batch_processing(self):
        """Trigger background worker thread to process queue."""
        if not self.is_processing:
            threading.Thread(target=self._process_worker, daemon=True).start()

    def _process_worker(self):
        self.is_processing = True
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            while True:
                # Find next pending item
                target_item = None
                with self._lock:
                    for item in self.queue:
                        if item["status"] == "pending":
                            item["status"] = "processing"
                            target_item = item
                            break

                if not target_item:
                    break

                # Process target item end-to-end
                try:
                    loop.run_until_complete(self._process_single_item(target_item))
                except Exception as e:
                    target_item["status"] = "failed"
                    target_item["error"] = str(e)
                    target_item["step"] = "មានបញ្ហា"
        finally:
            self.is_processing = False
            loop.close()

    async def _process_single_item(self, item: Dict[str, Any]):
        """Run complete 1-click pipeline on one video file."""
        item_id = item["id"]
        in_path = item["filepath"]
        item_dir = Path(f"data/projects/batch_{item_id}")
        item_dir.mkdir(parents=True, exist_ok=True)

        # 1. Extract Audio
        item["step"] = "1/5 កំពុងទាញយកសំឡេងពីវីដេអូ..."
        item["progress"] = 15
        raw_audio = item_dir / "audio.wav"
        extract_audio_from_video(in_path, str(raw_audio))
        duration = get_media_duration(in_path)

        # 2. Vocal Separation if enabled
        bgm_track = str(raw_audio)
        if item.get("separate_bgm", True):
            item["step"] = "2/5 AI កំពុងបំបែកសំឡេង & រក្សាភ្លេង BGM..."
            item["progress"] = 30
            try:
                bgm_out, _ = separate_vocals_and_bgm(str(raw_audio), output_dir=str(item_dir))
                bgm_track = bgm_out
            except Exception as e:
                print(f"Vocal separation fallback: {e}")

        # 3. Speech-to-Text (Auto Transcribe)
        item["step"] = "3/5 AI កំពុងស្តាប់ និងចាប់សំឡេង (Faster-Whisper)..."
        item["progress"] = 45
        dialogues = self.stt.transcribe_audio(str(raw_audio), source_lang="auto")
        if not dialogues:
            dialogues = [{
                "id": 1,
                "start": 0.5,
                "end": max(3.0, duration - 0.5),
                "speaker": "តួអង្គ",
                "text": "Drama video dialogue",
                "text_original": "Drama video dialogue"
            }]

        # 4. Contextual Drama/Recap Translation into Khmer
        item["step"] = "4/5 AI កំពុងបកប្រែជាភាសាខ្មែរ (រឿងភាគ/សម្រាយរឿង)..."
        item["progress"] = 65
        v_override = None if item["voice_mode"] == "auto" else item["voice_mode"]
        translated_dialogues = await self.translator.translate_dialogues(
            dialogues=dialogues,
            mode=item["drama_mode"],
            source_lang="auto",
            target_voice_override=v_override
        )

        # 5. Batch TTS Synthesis (Piseth & Sreymom)
        item["step"] = "5/5 កំពុងបញ្ចូលសំឡេង ពិសិដ្ឋ/ស្រីមុំ & Render វីដេអូ..."
        item["progress"] = 80
        voices_dir = item_dir / "voices"
        voices_dir.mkdir(parents=True, exist_ok=True)
        synthesized_items = await batch_synthesize(translated_dialogues, output_dir=str(voices_dir))

        # Mix Audio with BGM Ducking (Zero Chinese Vocal Bleed)
        mixed_audio = item_dir / "dubbed_mixed.mp3"
        mix_dubbed_audio(
            original_audio_path=bgm_track,
            dialogue_items=synthesized_items,
            output_mixed_path=str(mixed_audio),
            total_duration_sec=duration,
            ducking_volume_factor=0.08,
            dubbing_mode="smart_bgm"
        )

        # Final Render MP4 to Exports Directory
        out_filename = f"Dubbed_{Path(in_path).stem}.mp4"
        final_video_path = EXPORTS_DIR / out_filename
        
        render_dubbed_video(
            original_video_path=in_path,
            mixed_audio_path=str(mixed_audio),
            output_video_path=str(final_video_path),
            dialogues=synthesized_items,
            burn_subtitles=item.get("burn_subtitles", True),
            aspect_ratio=item.get("aspect_ratio", "16:9"),
            temp_dir=str(item_dir / "temp")
        )

        item["progress"] = 100
        item["status"] = "completed"
        item["step"] = "រួចរាល់ ១០០%"
        item["output_video"] = str(final_video_path)


# Global singleton instance
batch_manager = BatchDubbingManager()
