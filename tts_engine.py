"""
Khmer Neural TTS Engine for Piseth and Sreymom voices using Edge-TTS
"""
import os
import re
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


KHMER_DIGITS_MAP = {
    '០': '0', '១': '1', '២': '2', '៣': '3', '៤': '4',
    '៥': '5', '៦': '6', '៧': '7', '៨': '8', '៩': '9'
}

PHONETIC_ACRONYMS = [
    # Business & Roles
    (r'\b(?:CEO|Ceo|ceo)\b', 'លោកប្រធាន'),
    (r'\b(?:BOSS|Boss|boss)\b', 'ចៅហ្វាយ'),
    (r'\b(?:VIP|Vip|vip)\b', 'វីអាយភី'),
    (r'\b(?:MANAGER|Manager|manager)\b', 'អ្នកគ្រប់គ្រង'),
    (r'\b(?:DIRECTOR|Director|director)\b', 'នាយក'),
    (r'\b(?:PRESIDENT|President|president)\b', 'ប្រធាន'),

    # Tech, Media & Security
    (r'\b(?:DNA|Dna|dna)\b', 'ឌីអិនអេ'),
    (r'\b(?:GPS|Gps|gps)\b', 'ជីភីអេស'),
    (r'\b(?:CCTV|Cctv|cctv)\b', 'កាមេរ៉ាសុវត្ថិភាព'),
    (r'\b(?:KTV|Ktv|ktv)\b', 'ខេធីវី'),
    (r'\b(?:SIM|Sim|sim)\s*(?:CARD|Card|card)?\b', 'ស៊ីមកាត'),
    (r'\b(?:APP|App|app)\b', 'កម្មវិធី'),
    (r'\b(?:WIFI|Wifi|Wi-Fi|wifi)\b', 'វ៉ាយហ្វាយ'),
    (r'\b(?:ID|Id|id)\s*(?:CARD|Card|card)?\b', 'អាយឌី'),
    (r'\b(?:SOS|Sos|sos)\b', 'ជួយសង្គ្រោះបន្ទាន់'),
    (r'\b(?:PUBG|Pubg|GAME|Game|game)\b', 'ហ្គេម'),
    (r'\b(?:LIVE|Live|live)\b', 'ឡាយ'),
    (r'\b(?:POST|Post|post)\b', 'ផុស'),
    (r'\b(?:SHARE|Share|share)\b', 'ស៊ែរ'),
    (r'\b(?:LIKE|Like|like)\b', 'ឡាច'),
    (r'\b(?:COMMENT|Comment|comment)\b', 'ខមិន'),
    (r'\b(?:FAN|Fan|fan)\b', 'ហ្វេន'),
    (r'\b(?:FOLLOW|Follow|follow)\b', 'ហ្វូឡូ'),

    # Daily Drama Lifestyle & Places
    (r'\b(?:SPA|Spa|spa)\b', 'ស្ប៉ា'),
    (r'\b(?:WC|Wc|wc)\b', 'បន្ទប់ទឹក'),
    (r'\b(?:HOTEL|Hotel|hotel)\b', 'សណ្ឋាគារ'),
    (r'\b(?:BAR|Bar|bar)\b', 'បារ'),
    (r'\b(?:CLUB|Club|club)\b', 'ក្លឹប'),
    (r'\b(?:COFFEE|Coffee|coffee|CAFE|Cafe|cafe)\b', 'កាហ្វេ'),
    (r'\b(?:PARTY|Party|party)\b', 'ពិធីជប់លៀង'),
    (r'\b(?:SHOPPING|Shopping|shopping)\b', 'ដើរទិញឥវ៉ាន់'),
    (r'\b(?:CAR|Car|car)\b', 'ឡាន'),
    (r'\b(?:PHOTO|Photo|photo)\b', 'រូបថត'),
    (r'\b(?:CALL|Call|call)\b', 'ទូរស័ព្ទ'),
    (r'\b(?:MONEY|Money|money)\b', 'លុយ'),
    (r'\b(?:GIRLFRIEND|Girlfriend|GF|Gf|gf)\b', 'សង្សារស្រី'),
    (r'\b(?:BOYFRIEND|Boyfriend|BF|Bf|bf)\b', 'សង្សារប្រុស'),
    (r'\b(?:LOVE|Love|love)\b', 'ស្រឡាញ់'),
    (r'\b(?:OK|Ok|ok|O\.K\.)\b', 'អូខេ'),
    (r'\b(?:BYE|Bye|bye|GOODBYE|Goodbye)\b', 'លាសិនហើយ'),
    (r'\b(?:HI|Hi|hi|HELLO|Hello|hello)\b', 'សួស្តី'),
    (r'\b(?:YES|Yes|yes)\b', 'បាទ'),
    (r'\b(?:NO|No|no)\b', 'ទេ'),
    (r'\b(?:SORRY|Sorry|sorry)\b', 'សុំទោស'),
    (r'\b(?:THANK|Thank|THANKS|Thanks|thank you)\b', 'អរគុណ'),
]

# Syllable and word spacing rules for crisp, clear Khmer articulation in Edge-TTS
PHONETIC_ARTICULATION_RULES = [
    # Character names
    (r'លីនចាវចាវ|លីន​ចាវចាវ|Lin Zaozao|LinZaozao', 'លីន ចាវចាវ'),
    (r'លីមូឈាន|លី​មូឈាន|Li Muqian|LiMuqian', 'លី មូឈាន'),
    (r'សិនម៉ាន់លីង|ស៊ិនម៉ាន់លីន|Shen Manlin|ShenManlin', 'សិន ម៉ាន់លីង'),
    (r'ចាងចាវ|ចាង​ចាវ|Zhang Zhao|ZhangZhao', 'ចាង ចាវ'),
    (r'បងថ្លៃស្រីលីន|បងថ្លៃស្រី​លីន', 'បងថ្លៃស្រី លីន'),

    # Frequent drama compounds that sound muffled when attached
    (r'មនុស្សល្ងង់', 'មនុស្ស ល្ងង់'),
    (r'កូនក្នុងពោះ', 'កូន ក្នុងពោះ'),
    (r'កូននាគរាជ', 'កូន នាគរាជ'),
    (r'ហាងម៉ាស្សា', 'ហាង ម៉ាស្សា'),
    (r'បិទមាត់', 'បិទ មាត់'),
    (r'ឈប់ភ្លាម', 'ឈប់ ភ្លាម'),
    (r'ចេញទៅ', 'ចេញ ទៅ'),
    (r'សុំទោស', 'សុំ ទោស'),
    (r'អរគុណ', 'អរ គុណ'),
    (r'កុំបារម្ភ', 'កុំ បារម្ភ'),
    (r'ជួយផង', 'ជួយ ផង'),
    (r'ពិតមែនទេ', 'ពិត មែនទេ'),
    (r'ស្អីគេហ្នឹង', 'ស្អីគេ ហ្នឹង'),
    (r'យ៉ាងម៉េចដែរ', 'យ៉ាងម៉េច ដែរ'),
    (r'ម៉ាក់ក្មេក', 'ម៉ាក់ ក្មេក'),
    (r'ម្តាយក្មេក', 'ម្តាយ ក្មេក'),
    (r'ឪពុកក្មេក', 'ឪពុក ក្មេក'),
    (r'លោកប្រធាន', 'លោក ប្រធាន'),
]

def int_to_khmer_words(n: int) -> str:
    """Converts positive integer up to trillions into natural spoken Khmer words."""
    if n == 0:
        return 'សូន្យ'
    if n < 0:
        return 'ដក ' + int_to_khmer_words(abs(n))

    units = ['', 'មួយ', 'ពីរ', 'បី', 'បួន', 'ប្រាំ', 'ប្រាំមួយ', 'ប្រាំពីរ', 'ប្រាំបី', 'ប្រាំបួន']
    tens = ['', 'ដប់', 'ម្ភៃ', 'សាមសិប', 'សែសិប', 'ហាសិប', 'ហុកសិប', 'ចិតសិប', 'ប៉ែតសិប', 'កៅសិប']

    if n < 10:
        return units[n]
    if n < 100:
        ten = n // 10
        unit = n % 10
        if unit == 0:
            return tens[ten]
        return f"{tens[ten]}{units[unit]}"
    if n < 1000:
        hundred = n // 100
        rem = n % 100
        base = f"{units[hundred]}រយ"
        if rem == 0:
            return base
        return f"{base} {int_to_khmer_words(rem)}"
    if n < 10000:
        thousand = n // 1000
        rem = n % 1000
        base = f"{units[thousand]}ពាន់"
        if rem == 0:
            return base
        return f"{base} {int_to_khmer_words(rem)}"
    if n < 100000:
        ten_thousand = n // 10000
        rem = n % 10000
        base = f"{int_to_khmer_words(ten_thousand)}ម៉ឺន"
        if rem == 0:
            return base
        return f"{base} {int_to_khmer_words(rem)}"
    if n < 1000000:
        hundred_thousand = n // 100000
        rem = n % 100000
        base = f"{int_to_khmer_words(hundred_thousand)}សែន"
        if rem == 0:
            return base
        return f"{base} {int_to_khmer_words(rem)}"
    if n < 1000000000:
        million = n // 1000000
        rem = n % 1000000
        base = f"{int_to_khmer_words(million)}លាន"
        if rem == 0:
            return base
        return f"{base} {int_to_khmer_words(rem)}"
    if n < 1000000000000:
        billion = n // 1000000000
        rem = n % 1000000000
        base = f"{int_to_khmer_words(billion)}កោដិ"
        if rem == 0:
            return base
        return f"{base} {int_to_khmer_words(rem)}"
    return str(n)


def convert_numbers_in_text(text: str) -> str:
    """Finds numbers in various formats and converts them into spoken Khmer words."""
    # 0. Convert Khmer digits to Arabic digits
    for k, v in KHMER_DIGITS_MAP.items():
        text = text.replace(k, v)

    # 1. Clean formatted numbers: 500,000 or 500 000 -> 500000
    text = re.sub(r'(\d+),(\d{3})\b', r'\1\2', text)
    text = re.sub(r'(\d+),(\d{3})\b', r'\1\2', text)
    text = re.sub(r'(\d{1,4})\s+(\d{3})\b', r'\1\2', text)
    text = re.sub(r'(\d{1,4})\s+(\d{3})\b', r'\1\2', text)

    # 2. Chinese Wan (万 / ម៉ឺន)
    def _replace_wan(m):
        val = int(m.group(1))
        return f" {int_to_khmer_words(val * 10000)} "
    text = re.sub(r'(\d+)\s*(?:万|萬|ម៉ឺន)', _replace_wan, text)

    # 3. Currency Dollars ($)
    def _replace_dollar(m):
        num_str = m.group(1) or m.group(2)
        return f" {int_to_khmer_words(int(num_str))} ដុល្លារ "
    text = re.sub(r'\$\s*(\d+)|(\d+)\s*(?:ដុល្លារ|\$|USD)', _replace_dollar, text, flags=re.IGNORECASE)

    # 4. Currency Khmer Riel (៛ / រៀល)
    def _replace_riel(m):
        return f" {int_to_khmer_words(int(m.group(1)))} រៀល "
    text = re.sub(r'(\d+)\s*(?:៛|រៀល|KHR)', _replace_riel, text, flags=re.IGNORECASE)

    # 5. Currency Chinese Yuan (块 / 元 / យ័ន)
    def _replace_yuan(m):
        return f" {int_to_khmer_words(int(m.group(1)))} យ័ន "
    text = re.sub(r'(\d+)\s*(?:块|元|យ័ន|RMB)', _replace_yuan, text, flags=re.IGNORECASE)

    # 6. Ordinals (ទី 1, ទី1)
    def _replace_ordinal(m):
        num = int(m.group(1))
        return f" ទី{int_to_khmer_words(num)} "
    text = re.sub(r'ទី\s*(\d+)', _replace_ordinal, text)

    # 7. Percentage (50%, 99.9%)
    def _replace_percent(m):
        int_part = int(m.group(1))
        dec_part = m.group(2)
        if dec_part:
            dec_words = ' '.join([int_to_khmer_words(int(d)) for d in dec_part])
            return f" {int_to_khmer_words(int_part)} ក្បៀស {dec_words} ភាគរយ "
        return f" {int_to_khmer_words(int_part)} ភាគរយ "
    text = re.sub(r'(\d+)(?:\.(\d+))?\s*%', _replace_percent, text)

    # 8. Decimals (3.5, 0.5)
    def _replace_decimal(m):
        int_part = int(m.group(1))
        dec_part = m.group(2)
        dec_words = ' '.join([int_to_khmer_words(int(d)) for d in dec_part])
        return f" {int_to_khmer_words(int_part)} ក្បៀស {dec_words} "
    text = re.sub(r'\b(\d+)\.(\d+)\b', _replace_decimal, text)

    # 9. Standalone Integers
    def _replace_num(m):
        num_str = m.group(0)
        try:
            val = int(num_str)
            return f" {int_to_khmer_words(val)} "
        except Exception:
            return num_str
    text = re.sub(r'\b\d{1,12}\b', _replace_num, text)

    return re.sub(r'\s{2,}', ' ', text).strip()


def prepare_khmer_phonetic_for_speech(text: str) -> str:
    """
    Advanced Phonetic Pre-Processor for Edge-TTS (Piseth & Sreymom):
    1. Expands English acronyms & loanwords (CEO, VIP, DNA, KTV) into natural Khmer phonetic speech.
    2. Converts all numbers (formatted integers, decimals, currencies, percentages) into spoken Khmer words.
    3. Applies word boundary and syllable spacing rules so Edge-TTS articulates each word crisply without slurring.
    4. Enforces SINGLE CONTINUOUS BREATH (១ ដង្ហើមជាប់គ្នា): Strips all internal commas & mid-sentence pauses.
    5. Formats exactly ONE expressive ending mark (?!, ?, !, or ។) for confident, natural vocal delivery.
    """
    if not text:
        return ""
    res = text.strip()

    # 1. Expand English Acronyms & Loanwords (CEO, VIP, DNA, KTV, etc.)
    for pat, repl in PHONETIC_ACRONYMS:
        res = re.sub(pat, f" {repl} ", res)

    # 2. Convert Arabic & Khmer numbers, decimals, currencies to spoken Khmer words
    res = convert_numbers_in_text(res)

    # 3. Apply Phonetic Word & Syllable Spacing Rules for crystal-clear articulation
    for pat, repl in PHONETIC_ARTICULATION_RULES:
        res = re.sub(pat, f" {repl} ", res)

    # 4. SINGLE CONTINUOUS BREATH ENFORCEMENT (១ ដង្ហើមជាប់គ្នា):
    # Strip all internal mid-sentence commas, pauses, brackets, and quotes
    # so the voice actor delivers the entire line in ONE seamless, uninterrupted breath!
    res = re.sub(r'[,，、:：;；—–_~]+', ' ', res)
    res = re.sub(r'[（）\(\)\[\]{}"“\'”`]+', ' ', res)

    # Detect emotional punctuation intent from text
    has_question = any(q in res for q in ['?', '？', 'មែនទេ', 'ស្អី', 'អ្វី', 'នរណា', 'អ្នកណា', 'ម៉េច', 'យ៉ាងម៉េច', 'រឿងអី', 'ឯណា'])
    is_exclamation = any(e in res for e in ['!', '！', 'ភ្លាម', 'ឆាប់', 'ឈប់', 'រត់', 'កុំ', 'ជួយ', 'ហ៊ាន', 'ងាប់', 'បិទមាត់', 'ចេញ'])

    # Strip any internal or trailing punctuation marks and normalize whitespace
    res = re.sub(r'[!！?？។.\s]+', ' ', res).strip()

    # Append exactly ONE final ending punctuation for the entire single-breath utterance
    if has_question and is_exclamation:
        res += '?!'
    elif has_question:
        res += '?'
    elif is_exclamation:
        res += '!'
    else:
        res += '។'

    return res


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

    # Advanced Phonetic Articulation Pre-Processing for crystal-clear, articulate speech:
    cleaned_text = prepare_khmer_phonetic_for_speech(cleaned_text)

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

    # Retry up to 3 times for reliable synthesis with strict timeout
    last_err = None
    for attempt in range(1, 4):
        try:
            communicate = edge_tts.Communicate(
                text=cleaned_text,
                voice=voice_id,
                rate=rate_str,
                pitch=pitch_str
            )
            # Strict 10.0s timeout to prevent hanging on dropped websockets (lines 46 & 86)
            await asyncio.wait_for(communicate.save(str(final_output)), timeout=10.0)
            if final_output.exists() and final_output.stat().st_size > 100:
                return str(final_output)
        except Exception as e:
            last_err = e
            await asyncio.sleep(0.4 * attempt)

    if final_output.exists() and final_output.stat().st_size > 100:
        return str(final_output)

    # Resilient fallback to silent placeholder so the dubbing pipeline NEVER crashes mid-way
    print(f"Warning: Edge-TTS synthesis failed for line '{cleaned_text[:30]}...': {last_err}. Using fallback audio.")
    try:
        from pydub import AudioSegment
        silence = AudioSegment.silent(duration=1200)
        silence.export(str(final_output), format="mp3")
        return str(final_output)
    except Exception:
        raise RuntimeError(f"Edge-TTS synthesis failed after 3 attempts: {last_err}")


def trim_and_fit_voice_audio(audio_path: str, max_duration_sec: Optional[float] = None) -> float:
    """
    Strip leading/trailing dead silence with zero attack latency, apply studio vocal mastering (EQ/compressor),
    and time-fit audio to dialogue window so speech finishes in sync with character mouth closure.
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
        # Tight -38dB threshold so speech attacks at 0.0s immediately with zero lag
        s_trim = detect_leading_silence(seg, silence_threshold=-38.0)
        e_trim = detect_leading_silence(seg.reverse(), silence_threshold=-38.0)
        dur = len(seg)
        if (s_trim + e_trim) < dur:
            start_pos = s_trim  # Zero attack latency: audio starts instantly with character!
            end_pos = min(dur, dur - e_trim + 15)
            trimmed = seg[start_pos:end_pos]
        else:
            trimmed = seg

        trimmed_sec = len(trimmed) / 1000.0
        save_audio_safely(trimmed, str(audio_path))

        # Precision time-fitting: Clamp speed_ratio to max 1.18 to eliminate panicked/rushed speech ("ស្លន់ស្លោ")
        speed_ratio = 1.0
        if max_duration_sec and max_duration_sec > 0.3 and trimmed_sec > max_duration_sec:
            speed_ratio = min(1.18, max(0.95, trimmed_sec / max_duration_sec))

        # Apply Studio Vocal EQ, Highpass, and Broadcast Compression Chain
        enhance_voice_clarity_studio(str(audio_path), speed_ratio=speed_ratio)

        final_res = load_audio_safely(audio_path)
        # Clean soft fade-out if audio slightly overruns character's speaking window
        if max_duration_sec and len(final_res) > int((max_duration_sec + 0.06) * 1000):
            target_ms = int((max_duration_sec + 0.06) * 1000)
            final_res = final_res[:target_ms].fade_out(35)
            save_audio_safely(final_res, str(audio_path))

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
    semaphore = asyncio.Semaphore(3)

    async def _process_item(item: Dict[str, Any], index: int) -> Dict[str, Any]:
        async with semaphore:
            # Smooth network pacing to prevent Edge-TTS socket resets at line 46/86
            if index > 0 and index % 10 == 0:
                await asyncio.sleep(0.15)
            item_id = item.get("id", index)
            text = (item.get("text_km") or item.get("text", "")).strip()
            voice = item.get("voice") or default_voice
            rate = int(item.get("rate_percent", 0))
            pitch = int(item.get("pitch_hz", 0))

            # Calculate target dialogue window anchored strictly to character speaking duration
            start = float(item.get("start", 0.0))
            end = float(item.get("end", start + 2.0))
            char_dur = max(0.4, end - start)

            if index + 1 < len(dialogue_items):
                next_start = float(dialogue_items[index + 1].get("start", end + 1.0))
                # Lip-sync: anchor strictly to character duration, never exceed next_start
                target_window = min(max(0.4, next_start - start - 0.04), char_dur)
            else:
                target_window = char_dur

            # Dynamic Speech Rate Pre-calculation (CPS: characters per second):
            # Pre-set native Edge-TTS synthesis speed based on dialogue density
            if len(text) > 0 and char_dur > 0:
                cps = len(text) / char_dur
                if cps >= 15.0:
                    rate = max(rate, 18)   # +18% fast urgent dialogue
                elif cps >= 12.5:
                    rate = max(rate, 12)   # +12% brisk dialogue
                elif cps >= 10.5:
                    rate = max(rate, 6)    # +6% lively dialogue
                elif cps <= 6.0 and char_dur >= 2.0 and rate == 0:
                    rate = -4              # -4% calm measured pace

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
                item_copy["orig_start"] = start
                item_copy["orig_end"] = orig_end
                if index + 1 < len(dialogue_items):
                    item_copy["end"] = min(calculated_end, round(next_start - 0.04, 2))
                else:
                    item_copy["end"] = calculated_end
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
