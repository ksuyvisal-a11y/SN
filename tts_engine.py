"""
Khmer Neural TTS Engine for Piseth and Sreymom voices using Edge-TTS
"""
import os
import asyncio
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List
import edge_tts

# Supported Khmer Voices
VOICES = {
    "piseth": {
        "id": "km-KH-PisethNeural",
        "name": "ពិសិដ្ឋ (Piseth)",
        "gender": "Male",
        "role": "តួប្រុស / អ្នកសម្រាយរឿង (Male Lead / Recap Narrator)",
        "description": "សំឡេងប្រុសមាំ ច្បាស់ ល្អឥតខ្ចោះសម្រាប់តួប្រុស ឬអ្នករៀបរាប់សម្រាយសាច់រឿង",
        "avatar": "👨‍💼",
        "tag": "Male Neural"
    },
    "sreymom": {
        "id": "km-KH-SreymomNeural",
        "name": "ស្រីមុំ (Sreymom)",
        "gender": "Female",
        "role": "តួស្រី / មនោសញ្ចេតនា (Female Lead / Emotional)",
        "description": "សំឡេងស្រីស្រទន់ ពីរោះ រស់រវើក ល្អឥតខ្ចោះសម្រាប់តួស្រី និងឈុតមនោសញ្ចេតនា",
        "avatar": "👩‍💼",
        "tag": "Female Neural"
    }
}

CACHE_DIR = Path("cache/audio_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_voice_id(voice_key: str) -> str:
    """Resolve voice key ('piseth', 'sreymom', or full voice ID) to actual Edge-TTS voice name."""
    v_lower = str(voice_key).lower().strip()
    if v_lower in ("piseth", "male", "km-kh-pisethneural", "តួប្រុស", "ពិសិដ្ឋ"):
        return VOICES["piseth"]["id"]
    if v_lower in ("sreymom", "female", "km-kh-sreymomneural", "តួស្រី", "ស្រីមុំ"):
        return VOICES["sreymom"]["id"]
    return VOICES["piseth"]["id"]


def _format_rate(rate_percent: int) -> str:
    """Format speed rate percentage string, e.g. +10% or -15%."""
    if rate_percent >= 0:
        return f"+{rate_percent}%"
    return f"{rate_percent}%"


def _format_pitch(pitch_hz: int) -> str:
    """Format pitch string, e.g. +5Hz or -5Hz."""
    if pitch_hz >= 0:
        return f"+{pitch_hz}Hz"
    return f"{pitch_hz}Hz"


def _get_cache_filename(text: str, voice_id: str, rate: str, pitch: str) -> Path:
    """Generate deterministic hash filename for cached audio."""
    key = f"{text}_{voice_id}_{rate}_{pitch}".encode("utf-8")
    hash_str = hashlib.md5(key).hexdigest()
    return CACHE_DIR / f"{hash_str}.mp3"


async def synthesize_khmer_speech(
    text: str,
    voice: str = "piseth",
    rate_percent: int = 0,
    pitch_hz: int = 0,
    output_path: Optional[str] = None,
    use_cache: bool = True
) -> str:
    """
    Synthesize Khmer text into speech using Piseth or Sreymom voice.
    Returns the path to the generated MP3 file.
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty for TTS synthesis.")

    cleaned_text = text.strip()

    # Safety check: If text still contains Chinese/CJK characters and no Khmer, translate to Khmer first!
    has_cjk = any('\u4e00' <= char <= '\u9fff' for char in cleaned_text)
    has_khmer = any('\u1780' <= char <= '\u17ff' for char in cleaned_text)
    if has_cjk and not has_khmer:
        try:
            from translator import DramaTranslator
            trans = DramaTranslator()
            km_text = await trans.translate_text_free(cleaned_text, source_lang="zh-CN")
            if km_text and km_text.strip():
                cleaned_text = km_text.strip()
        except Exception as e:
            print(f"Fallback translation in TTS note: {e}")

    voice_id = get_voice_id(voice)
    rate_str = _format_rate(rate_percent)
    pitch_str = _format_pitch(pitch_hz)

    if output_path is None:
        if use_cache:
            cache_file = _get_cache_filename(cleaned_text, voice_id, rate_str, pitch_str)
            if cache_file.exists() and cache_file.stat().st_size > 500:
                return str(cache_file)
            final_output = cache_file
        else:
            final_output = CACHE_DIR / f"temp_{os.urandom(4).hex()}.mp3"
    else:
        final_output = Path(output_path)
        final_output.parent.mkdir(parents=True, exist_ok=True)

    # Retry up to 3 times for reliable synthesis
    last_err = None
    for attempt in range(1, 4):
        try:
            communicate = edge_tts.Communicate(
                text=cleaned_text,
                voice=voice_id,
                rate=rate_str,
                pitch=pitch_str
            )
            await communicate.save(str(final_output))
            if final_output.exists() and final_output.stat().st_size > 100:
                return str(final_output)
        except Exception as e:
            last_err = e
            await asyncio.sleep(0.6 * attempt)

    if final_output.exists() and final_output.stat().st_size > 100:
        return str(final_output)

    raise RuntimeError(f"Edge-TTS synthesis failed after 3 attempts: {last_err}")


def trim_and_fit_voice_audio(audio_path: str, max_duration_sec: Optional[float] = None) -> float:
    """
    Strip leading/trailing dead silence, apply studio vocal mastering (EQ/compressor),
    and time-fit audio to dialogue window so speech finishes in sync with character.
    """
    try:
        from audio_processor import (
            load_audio_safely,
            save_audio_safely,
            enhance_voice_clarity_studio,
            get_ffmpeg_path
        )
        from pydub.silence import detect_leading_silence

        seg = load_audio_safely(audio_path)
        s_trim = detect_leading_silence(seg, silence_threshold=-42.0)
        e_trim = detect_leading_silence(seg.reverse(), silence_threshold=-42.0)
        dur = len(seg)
        if (s_trim + e_trim) < dur:
            start_pos = max(0, s_trim - 10)
            end_pos = min(dur, dur - e_trim + 20)
            trimmed = seg[start_pos:end_pos]
        else:
            trimmed = seg

        trimmed_sec = len(trimmed) / 1000.0
        save_audio_safely(trimmed, str(audio_path))

        # Precision time-fitting if speech overshoots the character's speaking window
        speed_ratio = 1.0
        if max_duration_sec and max_duration_sec > 0.4 and trimmed_sec > max_duration_sec:
            speed_ratio = min(1.55, max(1.0, trimmed_sec / max_duration_sec))

        # Apply Studio Vocal EQ, Highpass, and Broadcast Compression Chain
        enhance_voice_clarity_studio(str(audio_path), speed_ratio=speed_ratio)

        final_res = load_audio_safely(audio_path)
        return len(final_res) / 1000.0
    except Exception as e:
        print(f"Voice trim/fit note: {e}")
        return 0.0


async def batch_synthesize(
    dialogue_items: List[Dict[str, Any]],
    output_dir: str,
    default_voice: str = "piseth"
) -> List[Dict[str, Any]]:
    """
    Synthesize dialogue items with dynamic rate estimation, studio vocal mastering,
    and tight lip-sync alignment so speech strictly matches the characters.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(4)

    async def _process_item(item: Dict[str, Any], index: int) -> Dict[str, Any]:
        async with semaphore:
            item_id = item.get("id", index)
            text = (item.get("text_km") or item.get("text", "")).strip()
            voice = item.get("voice") or default_voice
            rate = int(item.get("rate_percent", 0))
            pitch = int(item.get("pitch_hz", 0))

            # Calculate target dialogue window anchored to character speaking duration
            start = float(item.get("start", 0.0))
            end = float(item.get("end", start + 2.0))
            char_dur = max(0.5, end - start)

            if index + 1 < len(dialogue_items):
                next_start = float(dialogue_items[index + 1].get("start", end + 1.0))
                # Lip-sync sync: finish close to character's mouth closing, never exceed next_start
                target_window = min(max(0.5, next_start - start - 0.05), char_dur * 1.10 + 0.35)
            else:
                target_window = char_dur * 1.15 + 0.40

            # Dynamic Speech Rate Pre-calculation:
            # Khmer neural speech naturally averages ~10-11 characters/sec.
            # If line is dense relative to dialogue window, pre-boost rate so it sounds brisk and natural:
            if rate == 0 and len(text) > 0:
                est_duration = len(text) / 10.5
                if est_duration > char_dur * 1.08:
                    ratio = est_duration / char_dur
                    if ratio >= 1.40:
                        rate = 22  # +22% energetic drama pace
                    elif ratio >= 1.22:
                        rate = 15  # +15%
                    elif ratio >= 1.08:
                        rate = 8   # +8%

            line_audio_path = out_path / f"line_{index:04d}_{item_id}.mp3"
            try:
                audio_file = await synthesize_khmer_speech(
                    text=text,
                    voice=voice,
                    rate_percent=rate,
                    pitch_hz=pitch,
                    output_path=str(line_audio_path)
                )

                # Strip dead silence, apply studio vocal DSP, and time-fit to character window!
                final_dur = trim_and_fit_voice_audio(audio_file, target_window)

                item_copy = dict(item)
                item_copy["audio_file"] = audio_file
                item_copy["voice_used"] = voice
                item_copy["audio_duration"] = final_dur
                item_copy["rate_percent"] = rate
                calculated_end = round(start + final_dur, 2)
                orig_end = float(item.get("end", calculated_end))
                if index + 1 < len(dialogue_items):
                    item_copy["end"] = min(max(calculated_end, orig_end), round(next_start - 0.05, 2))
                else:
                    item_copy["end"] = max(calculated_end, orig_end)
                item_copy["success"] = True
                return item_copy
            except Exception as e:
                print(f"TTS line {index} error: {e}")
                item_copy = dict(item)
                item_copy["audio_file"] = None
                item_copy["error"] = str(e)
                item_copy["success"] = False
                return item_copy

    tasks = [_process_item(item, idx) for idx, item in enumerate(dialogue_items)]
    results = await asyncio.gather(*tasks)
    return results


def get_available_voices() -> Dict[str, Any]:
    """Returns available Khmer voices metadata."""
    return VOICES
