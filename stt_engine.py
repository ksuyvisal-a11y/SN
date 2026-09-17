"""
Multilingual AI Speech-to-Text (STT) Transcriber for Chinese, Korean, English, and Auto Detection
Optimized for Asian Dramas with Acoustic Pitch-Guided Speaker Diarization and Natural Sentence Merging
Strictly Two Professional Voices: ពិសិដ្ឋ (Piseth - Male Lead) and ស្រីមុំ (Sreymom - Female Lead)
"""
import os
import re
import io
import wave
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import imageio_ffmpeg
    FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG_EXE = "ffmpeg"

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False


def detect_segment_pitch(audio_path: str, start_s: float, end_s: float) -> float:
    """
    Detect fundamental pitch frequency (F0 in Hz) using autocorrelation.
    Accurately distinguishes Male (80-160Hz) vs Female (165-300Hz) dialogue turns.
    """
    if not NUMPY_AVAILABLE:
        return 0.0
    dur_s = end_s - start_s
    if dur_s <= 0.20:
        return 0.0
    try:
        cmd = [
            FFMPEG_EXE, '-ss', str(start_s), '-t', str(dur_s),
            '-i', str(audio_path), '-vn', '-ac', '1', '-ar', '16000',
            '-f', 'wav', '-'
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5)
        with wave.open(io.BytesIO(proc.stdout), 'rb') as wf:
            nframes = wf.getnframes()
            if nframes == 0:
                return 0.0
            raw = wf.readframes(nframes)
            samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32)

        frame_len = 1024
        hop = 512
        pitches = []
        min_lag = int(16000 / 320)  # 320 Hz
        max_lag = int(16000 / 80)   # 80 Hz

        for i in range(0, len(samples) - frame_len, hop):
            frame = samples[i:i + frame_len]
            frame = frame - np.mean(frame)
            energy = np.sum(frame ** 2)
            if energy < 1e5:
                continue
            corr = np.correlate(frame, frame, mode='full')
            corr = corr[len(corr) // 2:]
            if len(corr) <= max_lag:
                continue
            peak_lag = min_lag + np.argmax(corr[min_lag:max_lag])
            if corr[peak_lag] > 0.30 * corr[0]:
                f0 = 16000.0 / peak_lag
                pitches.append(f0)

        if pitches:
            return float(np.median(pitches))
    except Exception:
        pass
    return 0.0


class SpeechToTextEngine:
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self._model = None

    def _get_model(self):
        if self._model is None and FASTER_WHISPER_AVAILABLE:
            try:
                # Use int8 compute on CPU for fast, accurate lightweight transcription
                self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
            except Exception as e:
                print(f"Faster-whisper model load note: {e}")
                # Fallback to tiny if base had memory issue
                try:
                    self._model = WhisperModel("tiny", device="cpu", compute_type="int8")
                except Exception as e2:
                    print(f"Faster-whisper fallback failed: {e2}")
                    self._model = None
        return self._model

    def transcribe_audio(
        self,
        audio_path: str,
        source_lang: str = "auto",
        beam_size: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Transcribe audio file into timed dialogue segments with speaker continuity.
        Uses acoustic pitch detection and drama sentence consolidation to prevent fragmented lines.
        Returns list of dicts with: id, start, end, text, speaker, speaker_role, voice
        """
        model = self._get_model()
        if not model:
            raise RuntimeError(
                "AI Speech-to-Text model is not available. Please ensure faster-whisper is installed."
            )

        lang_code = None if source_lang in ("auto", "", None) else source_lang
        if lang_code in ("zh", "chinese", "mandarin"):
            lang_code = "zh"

        # Optimized VAD parameters: 650ms silence prevents breaking natural drama pauses
        segments_gen, info = model.transcribe(
            audio_path,
            language=lang_code,
            beam_size=beam_size,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=650, speech_pad_ms=250)
        )

        raw_segments = []
        for segment in segments_gen:
            text = segment.text.strip()
            if not text:
                continue
            raw_segments.append({
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": text
            })

        if not raw_segments:
            return []

        # 1. First Pass: Detect Speaker Turns and Roles using Acoustic Pitch & Semantic Cues
        speaker_segments = []
        current_speaker_title = "តួប្រុស (ពិសិដ្ឋ)"
        current_role = "male"
        current_voice = "piseth"

        for seg in raw_segments:
            text = seg["text"].strip()
            start = seg["start"]
            end = seg["end"]

            # Compute acoustic pitch from the audio segment
            pitch = detect_segment_pitch(audio_path, start, end)

            # Detect female vs male semantic cues
            female_kw = any(k in text for k in [
                "妈", "母亲", "夫人", "太太", "阿姨", "姑娘", "妹", "姐", "女儿",
                "丫头", "她", "奴婢", "臣妾", "本宫", "小姐", "婆婆", "媳妇", "女",
                "老板娘", "我老公"
            ])
            male_kw = any(k in text for k in [
                "爸", "父亲", "老爷", "老头", "哥", "弟", "男人", "兄弟", "他",
                "师兄", "陛下", "朕", "本王", "殿下", "执法官", "岳父", "相公", "我老婆"
            ])

            if pitch >= 165.0 or (pitch == 0.0 and female_kw and not male_kw):
                speaker_title = "តួស្រី (ស្រីមុំ)"
                detected_role = "female"
                voice = "sreymom"
            elif (0.0 < pitch < 165.0) or (pitch == 0.0 and male_kw and not female_kw):
                speaker_title = "តួប្រុស (ពិសិដ្ឋ)"
                detected_role = "male"
                voice = "piseth"
            else:
                # Maintain conversation continuity if pitch is ambiguous
                speaker_title = current_speaker_title
                detected_role = current_role
                voice = current_voice

            current_speaker_title = speaker_title
            current_role = detected_role
            current_voice = voice

            speaker_segments.append({
                "start": start,
                "end": end,
                "speaker": speaker_title,
                "detected_role": detected_role,
                "voice": voice,
                "pitch": round(pitch, 1),
                "text": text,
                "text_original": text
            })

        # 2. Second Pass: Consolidate segments of the SAME speaker into natural drama sentences
        # This prevents fragmented, clipped lines (បំបាត់ការបកខ្លីៗកំបុត)
        consolidated = []
        for seg in speaker_segments:
            if consolidated:
                prev = consolidated[-1]
                gap = round(seg["start"] - prev["end"], 2)
                combined_len = round(seg["end"] - prev["start"], 2)

                same_speaker = (prev["detected_role"] == seg["detected_role"])
                is_short_fragment = (seg["end"] - seg["start"] < 1.4) or (len(seg["text"]) <= 4)
                prev_is_short = (prev["end"] - prev["start"] < 1.4)

                # Merge conditions:
                # 1. Same character role (Piseth with Piseth, Sreymom with Sreymom)
                # 2. Total duration does not exceed 7.5s
                # 3. Gap <= 0.85s OR adjacent segment is a short fragment (gap <= 1.2s)
                should_merge = same_speaker and combined_len <= 7.5 and (
                    gap <= 0.85 or
                    (is_short_fragment and gap <= 1.2) or
                    (prev_is_short and gap <= 1.0)
                )

                if should_merge:
                    prev["end"] = seg["end"]
                    prev["text"] = f"{prev['text']} {seg['text']}".strip()
                    prev["text_original"] = prev["text"]
                    continue

            consolidated.append(dict(seg))

        # Re-number IDs and ensure clean properties
        for idx, item in enumerate(consolidated, start=1):
            item["id"] = idx
            item["rate_percent"] = 0
            item["pitch_hz"] = 0

        return consolidated
