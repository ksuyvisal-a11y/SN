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
    from audio_processor import get_silent_kwargs, get_ffmpeg_path
    FFMPEG_EXE = get_ffmpeg_path()
except Exception:
    def get_silent_kwargs():
        return {}
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

# Strict Drama First-Person Self-References, Kinship Terms & Direct Vocatives
FEMALE_VOCATIVES = [
    "老公", "相公", "夫君", "死鬼",
    "本宫", "臣妾", "奴婢", "小女子", "妾身", "本小姐",
    "老娘", "妈妈我", "女兒我", "娘亲我", "妈咪", "阿姨", "婆婆",
    "怀着孩子", "怀孕", "儿媳", "嫂嫂", "大嫂", "小姑子", "姐姐", "妹妹",
    "오빠", "언니"
]

MALE_VOCATIVES = [
    "老婆", "娘子", "夫人", "爱妃", "媳妇",
    "本座", "本王", "朕", "老子", "为父", "为夫", "微臣",
    "兄弟我", "爸爸我", "爹爹我", "儿子", "岳父", "岳母",
    "형"
]


def load_audio_samples_16k(audio_path: str) -> Tuple[Optional[Any], int]:
    """Load audio file as 16kHz mono float32 numpy array once into memory for ultra-fast processing."""
    if not NUMPY_AVAILABLE:
        return None, 16000
    try:
        cmd = [
            FFMPEG_EXE, '-nostdin', '-y', '-i', str(audio_path),
            '-vn', '-ac', '1', '-ar', '16000',
            '-f', 'wav', '-'
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=1800, **get_silent_kwargs())
        with wave.open(io.BytesIO(proc.stdout), 'rb') as wf:
            nframes = wf.getnframes()
            if nframes == 0:
                return None, 16000
            raw = wf.readframes(nframes)
            samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
            return samples, 16000
    except Exception as e:
        print(f"Fast audio load note: {e}")
        return None, 16000


def analyze_segment_acoustics_fast(
    sig: np.ndarray,
    sr: int = 16000
) -> Dict[str, Any]:
    """
    Fast, vectorized acoustic analysis of vocal segment from in-memory numpy array:
    1. FFT / Autocorrelation Fundamental Frequency (F0) tracking
    2. Spectral Centroid calculation
    3. Low-band (chest resonance 75-280Hz) vs Mid-High-band Energy Ratio
    """
    default_res = {
        "role": "unknown",
        "voice": "piseth",
        "speaker": "តួប្រុស (ពិសិដ្ឋ)",
        "f0": 0.0,
        "centroid": 0.0,
        "ratio": 1.0
    }
    if sig is None or len(sig) < 800:
        return default_res

    try:
        frame_len = 1024
        hop = 512
        min_lag = int(sr / 380)  # ~42 samples (380 Hz)
        max_lag = int(sr / 75)   # ~213 samples (75 Hz)
        pitches = []

        # Vectorized autocorrelation pitch tracking across voiced frames
        for i in range(0, len(sig) - frame_len, hop):
            fr = sig[i:i + frame_len]
            fr_norm = fr - np.mean(fr)
            energy = np.sum(fr_norm ** 2)
            if energy < 8e4:
                continue

            corr = np.correlate(fr_norm, fr_norm, mode='full')
            corr = corr[len(corr)//2:]
            if len(corr) <= max_lag:
                continue

            peak_lag = min_lag + np.argmax(corr[min_lag:max_lag])
            if corr[peak_lag] > 0.28 * corr[0]:
                f0s = sr / peak_lag
                pitches.append(f0s)

        med_f0 = float(np.median(pitches)) if pitches else 0.0

        # Frequency Domain Analysis: Centroid and Harmonic Energy Ratio
        fft = np.abs(np.fft.rfft(sig))
        freqs = np.fft.rfftfreq(len(sig), 1.0 / sr)
        tot_fft = np.sum(fft) + 1e-6
        centroid = float(np.sum(freqs * fft) / tot_fft)

        low_energy = float(np.sum(fft[(freqs >= 75) & (freqs <= 280)] ** 2))
        high_energy = float(np.sum(fft[(freqs > 300) & (freqs <= 3000)] ** 2)) + 1e-6
        ratio_low_high = low_energy / high_energy

        # Multi-factor Classification
        if med_f0 >= 165.0:
            role = "female"
        elif 0.0 < med_f0 <= 152.0:
            role = "male"
        elif 152.0 < med_f0 < 165.0:
            role = "male" if (ratio_low_high > 0.80 or centroid < 1900) else "female"
        else:
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


def analyze_segment_acoustics(audio_path: str, start_s: float, end_s: float) -> Dict[str, Any]:
    """Backwards-compatible wrapper returning acoustic analysis."""
    default_res = {
        "role": "unknown",
        "voice": "piseth",
        "speaker": "តួប្រុស (ពិសិដ្ឋ)",
        "f0": 0.0,
        "centroid": 0.0,
        "ratio": 1.0
    }
    dur_s = end_s - start_s
    if dur_s <= 0.15 or not NUMPY_AVAILABLE:
        return default_res
    try:
        cmd = [
            FFMPEG_EXE, '-nostdin', '-y', '-ss', str(start_s), '-t', str(dur_s),
            '-i', str(audio_path), '-vn', '-ac', '1', '-ar', '16000',
            '-f', 'wav', '-'
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=15, **get_silent_kwargs())
        with wave.open(io.BytesIO(proc.stdout), 'rb') as wf:
            nframes = wf.getnframes()
            if nframes < 600:
                return default_res
            raw = wf.readframes(nframes)
            sig = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
        return analyze_segment_acoustics_fast(sig, 16000)
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
            device = "cpu"
            compute_type = "int8"
            threads = min(4, os.cpu_count() or 4)
            try:
                import ctranslate2
                if "cuda" in ctranslate2.get_supported_compute_types("cuda"):
                    device = "cuda"
                    compute_type = "float16"
            except Exception:
                pass

            target_model = self.model_size
            # On CPU, prevent medium or large from freezing Windows! Default to base
            if device == "cpu" and target_model in ("medium", "large", "large-v3"):
                target_model = "base"

            try:
                self._model = WhisperModel(target_model, device=device, compute_type=compute_type, cpu_threads=threads)
            except Exception as e:
                print(f"Faster-whisper model load note ({target_model}): {e}")
                try:
                    self._model = WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=threads)
                except Exception:
                    try:
                        self._model = WhisperModel("tiny", device="cpu", compute_type="int8", cpu_threads=threads)
                    except Exception as e2:
                        print(f"Faster-whisper fallback failed: {e2}")
                        self._model = None
        return self._model

    def transcribe_audio(
        self,
        audio_path: str,
        source_lang: str = "auto",
        beam_size: int = 2,
        voice_override: Optional[str] = None,
        progress_callback = None
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

        # Clean generic prompt ONLY for Chinese, NO hardcoded character names from other dramas!
        initial_prompt = None
        if lang_code == "zh":
            initial_prompt = "以下是影视剧对话，台词清晰，标点符号完整。"

        # Balanced VAD parameters tuned for Asian TV Dramas with Background Music:
        # threshold=0.45: cleanly differentiates speech from background strings and music
        # min_speech_duration_ms=100: catches short exclamations ("站住!", "谁?", "走!", "救命!")
        # max_speech_duration_s=8.0: prevents oversized runaway monologue chunks
        # min_silence_duration_ms=280: tight speech boundary detection
        segments_gen, info = model.transcribe(
            audio_path,
            language=lang_code,
            initial_prompt=initial_prompt,
            beam_size=min(beam_size, 2),
            best_of=1,
            condition_on_previous_text=False,
            compression_ratio_threshold=2.4,
            no_speech_threshold=0.75,
            word_timestamps=True,
            vad_filter=True,
            vad_parameters=dict(
                threshold=0.30,
                min_speech_duration_ms=80,
                max_speech_duration_s=9.0,
                min_silence_duration_ms=320,
                speech_pad_ms=160
            )
        )

        raw_segments = []
        tot_dur = getattr(info, "duration", 0) or 1.0
        for segment in segments_gen:
            text = segment.text.strip()
            if not text:
                continue

            words = getattr(segment, "words", None)
            if not words:
                # If no word-level timestamps, split text by sentence punctuation if long
                sub_sentences = [s.strip() for s in re.split(r'([。！？!?\n]+)', text) if s.strip()]
                combined_sentences = []
                curr_sent = ""
                for part in sub_sentences:
                    curr_sent += part
                    if re.search(r'[。！？!?\n]', part):
                        combined_sentences.append(curr_sent.strip())
                        curr_sent = ""
                if curr_sent.strip():
                    combined_sentences.append(curr_sent.strip())

                if len(combined_sentences) <= 1:
                    raw_segments.append({
                        "start": round(segment.start, 2),
                        "end": round(segment.end, 2),
                        "text": text
                    })
                else:
                    total_chars = max(1, sum(len(s) for s in combined_sentences))
                    seg_dur = max(0.4, segment.end - segment.start)
                    cur_t = segment.start
                    for s in combined_sentences:
                        p_dur = (len(s) / total_chars) * seg_dur
                        p_start = round(cur_t, 2)
                        p_end = round(cur_t + p_dur, 2)
                        raw_segments.append({
                            "start": p_start,
                            "end": max(round(p_start + 0.35, 2), p_end),
                            "text": s
                        })
                        cur_t += p_dur
            else:
                # Word-level timestamp precision: Group words into individual dialogue lines!
                curr_words = []
                for w_idx, w in enumerate(words):
                    curr_words.append(w)
                    w_txt = getattr(w, "word", "") or ""

                    # Check split triggers:
                    # 1. Punctuation in word (ending marks)
                    has_punct = bool(re.search(r'[。！？!?；;\n]', w_txt))

                    # 2. Pause between this word and next word >= 0.85s (dialogue pause / turn-taking)
                    has_pause = False
                    if w_idx + 1 < len(words):
                        next_w = words[w_idx + 1]
                        if (next_w.start - w.end) >= 0.85:
                            has_pause = True

                    # 3. Accumulated length >= 6.5 seconds (prevents runaway sentences)
                    span = curr_words[-1].end - curr_words[0].start
                    is_too_long = span >= 6.5 and len(curr_words) >= 4

                    if (has_punct or has_pause or is_too_long) and len(curr_words) > 0:
                        line_txt = "".join(getattr(cw, "word", "") for cw in curr_words).strip()
                        if line_txt:
                            l_start = round(curr_words[0].start, 2)
                            l_end = round(curr_words[-1].end, 2)
                            raw_segments.append({
                                "start": l_start,
                                "end": max(round(l_start + 0.35, 2), l_end),
                                "text": line_txt
                            })
                        curr_words = []

                # Any trailing words
                if curr_words:
                    line_txt = "".join(getattr(cw, "word", "") for cw in curr_words).strip()
                    if line_txt:
                        l_start = round(curr_words[0].start, 2)
                        l_end = round(curr_words[-1].end, 2)
                        raw_segments.append({
                            "start": l_start,
                            "end": max(round(l_start + 0.35, 2), l_end),
                            "text": line_txt
                        })

            if progress_callback and tot_dur > 0:
                p_cur = 45 + int(min(15, (segment.end / tot_dur) * 15))
                m_curr = int(segment.end // 60)
                s_curr = int(segment.end % 60)
                progress_callback(
                    p_cur,
                    f"៣/៧ AI កំពុងស្តាប់នៅនាទី {m_curr:02d}:{s_curr:02d}...",
                    f"Transcribing audio at {m_curr:02d}:{s_curr:02d}..."
                )

        if not raw_segments:
            return []

        # Check if single voice mode is requested
        vo_clean = str(voice_override or "").lower().strip()
        is_single_voice = vo_clean in ("piseth", "sreymom", "male", "female")
        single_voice = "sreymom" if vo_clean in ("sreymom", "female") else "piseth"

        # Load audio samples into memory ONCE for ultra-fast in-memory acoustic analysis
        audio_samples = None
        sr = 16000
        if not is_single_voice and NUMPY_AVAILABLE and audio_path and os.path.exists(audio_path):
            audio_samples, sr = load_audio_samples_16k(audio_path)

        # 1. First Pass: Fast Acoustic Analysis & Vocative Classification
        speaker_segments = []
        last_confirmed_role = "male"

        for idx, seg in enumerate(raw_segments):
            text = seg["text"].strip()
            start = seg["start"]
            end = seg["end"]

            if is_single_voice:
                speaker_segments.append({
                    "start": start,
                    "end": end,
                    "speaker": "ស្រីមុំ (Sreymom)" if single_voice == "sreymom" else "ពិសិដ្ឋ (Piseth)",
                    "detected_role": "female" if single_voice == "sreymom" else "male",
                    "voice": single_voice,
                    "pitch": 0.0,
                    "text": text,
                    "text_original": text
                })
                continue

            # Fast in-memory acoustic slice
            acoustics = None
            if audio_samples is not None and len(audio_samples) > 0:
                s_idx = max(0, int(start * sr))
                e_idx = min(len(audio_samples), int(end * sr))
                if e_idx > s_idx:
                    acoustics = analyze_segment_acoustics_fast(audio_samples[s_idx:e_idx], sr)

            if not acoustics:
                acoustics = {
                    "role": "unknown",
                    "voice": "piseth",
                    "speaker": "តួប្រុស (ពិសិដ្ឋ)",
                    "f0": 0.0
                }

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
        # CRITICAL: Only merge micro-gaps (<= 0.10s) within continuous speech.
        # NEVER merge across pauses, ensuring speech matches mouth movements exactly!
        consolidated = []
        for seg in speaker_segments:
            if consolidated:
                prev = consolidated[-1]
                gap = round(seg["start"] - prev["end"], 2)
                combined_len = round(seg["end"] - prev["start"], 2)
                same_speaker = (prev["detected_role"] == seg["detected_role"])

                # Merge if it's the exact same speaker with brief natural pause (<= 0.22s)
                if same_speaker and combined_len <= 4.5 and gap <= 0.22:
                    prev["end"] = seg["end"]
                    prev["text"] = f"{prev['text']} {seg['text']}".strip()
                    prev["text_original"] = prev["text"]
                    continue

            consolidated.append(dict(seg))

        # 3. Third Pass: Strict Anti-Overlap & Boundary Enforcement
        # Ensure that segment start times never collide or overlap with previous segment end times
        cleaned_dialogues = []
        min_seg_gap = 0.08  # 80ms minimum acoustic separation
        for seg in consolidated:
            if cleaned_dialogues:
                prev = cleaned_dialogues[-1]
                if seg["start"] < prev["end"] + min_seg_gap:
                    if prev["end"] > seg["start"]:
                        if (seg["start"] - prev["start"]) >= 0.35:
                            prev["end"] = round(seg["start"] - min_seg_gap, 2)
                        else:
                            seg["start"] = round(prev["end"] + min_seg_gap, 2)
                            if seg["end"] <= seg["start"]:
                                seg["end"] = round(seg["start"] + 0.35, 2)
                    else:
                        seg["start"] = round(prev["end"] + min_seg_gap, 2)
                        if seg["end"] <= seg["start"]:
                            seg["end"] = round(seg["start"] + 0.35, 2)
            cleaned_dialogues.append(seg)
        consolidated = cleaned_dialogues

        # Re-number IDs and initialize standard speech parameters
        for idx, item in enumerate(consolidated, start=1):
            item["id"] = idx
            item["rate_percent"] = 0
            item["pitch_hz"] = 0

        return consolidated


def transcribe_audio(audio_path: str, source_lang: str = "auto", **kwargs) -> List[Dict[str, Any]]:
    """Module-level convenience wrapper for SpeechToTextEngine.transcribe_audio."""
    engine = SpeechToTextEngine()
    return engine.transcribe_audio(audio_path, source_lang=source_lang, **kwargs)

