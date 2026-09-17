"""
Multilingual AI Speech-to-Text (STT) Transcriber for Chinese, Korean, English, and Auto Detection
Optimized for Asian TV Dramas with Advanced Acoustic Speaker Diarization and Millisecond Lip-Sync Precision
Strictly Two Authentic Voices: ពិសិដ្ឋ (Piseth - Male Lead) and ស្រីមុំ (Sreymom - Female Lead)
"""
import os
import re
import io
import wave
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

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

# Strict Drama First-Person Self-References & Direct Spouse Vocatives
# NOTE: Third-person pronouns ("他", "她") and object nouns ("男人", "女人") are STRICTLY excluded
FEMALE_VOCATIVES = [
    "老公", "相公", "夫君", "死鬼",
    "本宫", "臣妾", "奴婢", "小女子", "妾身", "本小姐",
    "老娘", "妈妈我", "女兒我", "娘亲我",
    "오빠", "언니"
]

MALE_VOCATIVES = [
    "老婆", "娘子", "夫人", "爱妃", "媳妇",
    "本座", "本王", "朕", "老子", "为父", "为夫", "微臣",
    "兄弟我", "爸爸我", "爹爹我",
    "형"
]


def analyze_segment_acoustics(audio_path: str, start_s: float, end_s: float) -> Dict[str, Any]:
    """
    Multi-layered acoustic analysis of vocal segment:
    1. YIN-based Fundamental Frequency (F0) tracking (75Hz - 450Hz range)
    2. Spectral Centroid calculation
    3. Low-band (chest resonance 75-280Hz) vs Mid-High-band (vowel formants 300-3000Hz) Energy Ratio
    Accurately classifies Male vs Female speech with zero reliance on 3rd-person pronouns.
    """
    default_res = {
        "role": "unknown",
        "voice": "piseth",
        "speaker": "តួប្រុស (ពិសិដ្ឋ)",
        "f0": 0.0,
        "centroid": 0.0,
        "ratio": 1.0
    }
    if not NUMPY_AVAILABLE:
        return default_res

    dur_s = end_s - start_s
    if dur_s <= 0.15:
        return default_res

    try:
        cmd = [
            FFMPEG_EXE, '-ss', str(start_s), '-t', str(dur_s),
            '-i', str(audio_path), '-vn', '-ac', '1', '-ar', '16000',
            '-f', 'wav', '-'
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=6)
        with wave.open(io.BytesIO(proc.stdout), 'rb') as wf:
            nframes = wf.getnframes()
            if nframes < 600:
                return default_res
            raw = wf.readframes(nframes)
            sig = np.frombuffer(raw, dtype=np.int16).astype(np.float32)

        sr = 16000
        min_f0 = 75
        max_f0 = 450
        min_lag = int(sr / max_f0)  # ~35 samples
        max_lag = int(sr / min_f0)  # ~213 samples
        frame_len = 1024
        hop = 512
        threshold = 0.20
        f0s = []

        # YIN Pitch Tracking across voiced frames
        for i in range(0, len(sig) - frame_len - max_lag, hop):
            fr = sig[i:i + frame_len]
            fr_norm = fr - np.mean(fr)
            energy = np.sum(fr_norm ** 2)
            if energy < 8e4:
                continue

            d = np.zeros(max_lag + 1)
            for tau in range(1, max_lag + 1):
                diff = fr_norm - (sig[i + tau : i + tau + frame_len] - np.mean(sig[i + tau : i + tau + frame_len]))
                d[tau] = np.sum(diff ** 2)

            d_prime = np.zeros(max_lag + 1)
            d_prime[0] = 1.0
            running_sum = 0.0
            for tau in range(1, max_lag + 1):
                running_sum += d[tau]
                d_prime[tau] = d[tau] / (running_sum / tau) if running_sum > 0 else 1.0

            tau_choice = None
            for tau in range(min_lag, max_lag):
                if d_prime[tau] < threshold:
                    while tau + 1 < max_lag and d_prime[tau + 1] < d_prime[tau]:
                        tau += 1
                    tau_choice = tau
                    break

            if tau_choice is not None:
                f0s.append(sr / tau_choice)

        med_f0 = float(np.median(f0s)) if f0s else 0.0

        # Frequency Domain Analysis: Centroid and Harmonic Energy Ratio
        fft = np.abs(np.fft.rfft(sig))
        freqs = np.fft.rfftfreq(len(sig), 1.0 / sr)
        tot_fft = np.sum(fft) + 1e-6
        centroid = float(np.sum(freqs * fft) / tot_fft)

        low_energy = float(np.sum(fft[(freqs >= 75) & (freqs <= 280)] ** 2))
        high_energy = float(np.sum(fft[(freqs > 300) & (freqs <= 3000)] ** 2)) + 1e-6
        ratio_low_high = low_energy / high_energy

        # Multi-factor Classification
        if med_f0 >= 168.0:
            role = "female"
        elif 0.0 < med_f0 <= 152.0:
            role = "male"
        elif 152.0 < med_f0 < 168.0:
            # Borderline zone: use spectral energy balance
            role = "male" if (ratio_low_high > 0.80 or centroid < 1900) else "female"
        else:
            # Unvoiced/whispered: rely on frequency distribution
            if ratio_low_high >= 0.85 or centroid < 1900:
                role = "male"
            elif ratio_low_high <= 0.62 or centroid >= 2100:
                role = "female"
            else:
                role = "unknown"

        voice = "sreymom" if role == "female" else "piseth"
        speaker = "តួស្រី (ស្រីមុំ)" if role == "female" else "តួប្រុស (ពិសិដ្ឋ)"

        return {
            "role": role,
            "voice": voice,
            "speaker": speaker,
            "f0": round(med_f0, 1),
            "centroid": round(centroid, 1),
            "ratio": round(ratio_low_high, 2)
        }
    except Exception:
        return default_res


def detect_segment_pitch(audio_path: str, start_s: float, end_s: float) -> float:
    """Backwards-compatible wrapper returning fundamental pitch frequency in Hz."""
    return analyze_segment_acoustics(audio_path, start_s, end_s)["f0"]


class SpeechToTextEngine:
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self._model = None

    def _get_model(self):
        if self._model is None and FASTER_WHISPER_AVAILABLE:
            try:
                # Use int8 compute on CPU for fast, lightweight, and accurate transcription
                self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
            except Exception as e:
                print(f"Faster-whisper model load note: {e}")
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
        beam_size: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Transcribe audio file into timed dialogue segments with millisecond lip-sync accuracy.
        Applies acoustic multi-layered speaker identification and strict male/female distinction.
        Returns list of dicts with: id, start, end, text, speaker, detected_role, voice, pitch
        """
        model = self._get_model()
        if not model:
            raise RuntimeError(
                "AI Speech-to-Text model is not available. Please ensure faster-whisper is installed."
            )

        lang_code = None if source_lang in ("auto", "", None) else source_lang
        if lang_code in ("zh", "chinese", "mandarin"):
            lang_code = "zh"

        # Highly Sensitive VAD parameters tuned for Asian TV Dramas:
        # threshold=0.32: captures quiet, whispered, and rapid speech lines
        # min_speech_duration_ms=100: catches short exclamations ("站住!", "谁?", "走!", "救命!")
        # speech_pad_ms=180: preserves the initial vowel/consonant when mouth first opens
        # min_silence_duration_ms=350: ensures speech segments start and end exactly with dialogue
        segments_gen, info = model.transcribe(
            audio_path,
            language=lang_code,
            beam_size=beam_size,
            vad_filter=True,
            vad_parameters=dict(
                threshold=0.32,
                min_speech_duration_ms=100,
                max_speech_duration_s=12.0,
                min_silence_duration_ms=350,
                speech_pad_ms=180
            )
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

        # 1. First Pass: Independent Acoustic Analysis & Strict Vocative Classification
        speaker_segments = []
        last_confirmed_role = "male"

        for idx, seg in enumerate(raw_segments):
            text = seg["text"].strip()
            start = seg["start"]
            end = seg["end"]

            # Acoustic analysis on isolated audio segment
            acoustics = analyze_segment_acoustics(audio_path, start, end)
            detected_role = acoustics["role"]

            # Grammatical first-person & spouse vocatives check (strict)
            has_female_voc = any(kw in text for kw in FEMALE_VOCATIVES)
            has_male_voc = any(kw in text for kw in MALE_VOCATIVES)

            if has_female_voc and not has_male_voc:
                role = "female"
                voice = "sreymom"
                speaker_title = "តួស្រី (ស្រីមុំ)"
            elif has_male_voc and not has_female_voc:
                role = "male"
                voice = "piseth"
                speaker_title = "តួប្រុស (ពិសិដ្ឋ)"
            elif detected_role in ("female", "male"):
                role = detected_role
                voice = acoustics["voice"]
                speaker_title = acoustics["speaker"]
            else:
                # Ambiguous acoustic frame:
                # If there's a conversation turn gap (> 0.4s) from previous line, alternate speaker
                if speaker_segments:
                    prev_seg = speaker_segments[-1]
                    turn_gap = start - prev_seg["end"]
                    if turn_gap >= 0.40:
                        # Natural dialogue back-and-forth alternation
                        role = "female" if prev_seg["detected_role"] == "male" else "male"
                    else:
                        role = prev_seg["detected_role"]
                else:
                    role = last_confirmed_role

                voice = "sreymom" if role == "female" else "piseth"
                speaker_title = "តួស្រី (ស្រីមុំ)" if role == "female" else "តួប្រុស (ពិសិដ្ឋ)"

            if role in ("female", "male"):
                last_confirmed_role = role

            speaker_segments.append({
                "start": start,
                "end": end,
                "speaker": speaker_title,
                "detected_role": role,
                "voice": voice,
                "pitch": acoustics["f0"],
                "text": text,
                "text_original": text
            })

        # 2. Second Pass: Tight Lip-Sync Consolidation
        # CRITICAL: Only merge micro-gaps (<= 0.25s) within continuous speech.
        # NEVER merge across pauses > 0.25s, ensuring speech matches mouth movements exactly!
        consolidated = []
        for seg in speaker_segments:
            if consolidated:
                prev = consolidated[-1]
                gap = round(seg["start"] - prev["end"], 2)
                combined_len = round(seg["end"] - prev["start"], 2)
                same_speaker = (prev["detected_role"] == seg["detected_role"])

                # Only merge if it's the exact same speaker taking a micro-breath pause (<= 0.25s)
                if same_speaker and combined_len <= 5.5 and gap <= 0.25:
                    prev["end"] = seg["end"]
                    prev["text"] = f"{prev['text']} {seg['text']}".strip()
                    prev["text_original"] = prev["text"]
                    continue

            consolidated.append(dict(seg))

        # Re-number IDs and initialize standard speech parameters
        for idx, item in enumerate(consolidated, start=1):
            item["id"] = idx
            item["rate_percent"] = 0
            item["pitch_hz"] = 0

        return consolidated
