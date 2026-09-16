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
    voice_id = get_voice_id(voice)
    rate_str = _format_rate(rate_percent)
    pitch_str = _format_pitch(pitch_hz)

    if output_path is None:
        if use_cache:
            cache_file = _get_cache_filename(cleaned_text, voice_id, rate_str, pitch_str)
            if cache_file.exists() and cache_file.stat().st_size > 0:
                return str(cache_file)
            final_output = cache_file
        else:
            final_output = CACHE_DIR / f"temp_{os.urandom(4).hex()}.mp3"
    else:
        final_output = Path(output_path)
        final_output.parent.mkdir(parents=True, exist_ok=True)

    communicate = edge_tts.Communicate(
        text=cleaned_text,
        voice=voice_id,
        rate=rate_str,
        pitch=pitch_str
    )
    
    await communicate.save(str(final_output))
    return str(final_output)


async def batch_synthesize(
    dialogue_items: List[Dict[str, Any]],
    output_dir: str,
    default_voice: str = "piseth"
) -> List[Dict[str, Any]]:
    """
    Synthesize a list of dialogue items concurrently.
    Each item in dialogue_items should have:
    - id: int/str
    - text: str (Khmer text)
    - voice: str (optional, 'piseth' or 'sreymom')
    - rate_percent: int (optional)
    - pitch_hz: int (optional)
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    async def _process_item(item: Dict[str, Any], index: int) -> Dict[str, Any]:
        item_id = item.get("id", index)
        text = item.get("text_km") or item.get("text", "")
        voice = item.get("voice") or default_voice
        rate = item.get("rate_percent", 0)
        pitch = item.get("pitch_hz", 0)

        line_audio_path = out_path / f"line_{index:04d}_{item_id}.mp3"
        try:
            audio_file = await synthesize_khmer_speech(
                text=text,
                voice=voice,
                rate_percent=rate,
                pitch_hz=pitch,
                output_path=str(line_audio_path)
            )
            item_copy = dict(item)
            item_copy["audio_file"] = audio_file
            item_copy["voice_used"] = voice
            item_copy["success"] = True
            return item_copy
        except Exception as e:
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
