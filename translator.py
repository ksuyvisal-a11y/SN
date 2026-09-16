"""
Drama & Movie Recap Contextual Translation Engine for Chinese, Korean, English -> Khmer
"""
import os
import re
import json
import httpx
from typing import List, Dict, Any, Optional

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

DRAMA_PROMPT_SYSTEM = """You are a master Khmer film translator and voice-over script writer specializing in Asian dramas (Chinese, Korean, Thai) and Hollywood movies.
Your goal is to translate dialogue/scripts from Chinese, Korean, or English into natural, emotional, and captivating Khmer language.

Rules for Khmer Drama Dubbing & Facebook Recap:
1. Natural Flow: Use natural spoken Khmer phrasing that sounds great when spoken aloud by voice actors (Piseth & Sreymom).
2. Proper Khmer Pronouns:
   - Male Lead / Hero -> ខ្ញុំ, បង, លោក
   - Female Lead / Heroine -> ខ្ញុំ, អូន, នាង
   - Royalty / Historical -> ព្រះអង្គ, ព្រះនាង, ម្ចាស់បង, ទូលបង្គំ, លោកម្ចាស់
   - Enemies / Action -> ឯង, អញ, ពួកឯង
   - Friends / Casual -> ពួកយើង, ឯង, គ្នា
3. For Facebook Movie Recap mode:
   - Use engaging storyteller narration tone (e.g., "នៅថ្ងៃមួយ...", "ស្រាប់តែពេលនោះ...", "ទោះបីជាយ៉ាងណា...").
4. Character Role / Voice Assignment:
   - Assign 'piseth' for Male characters, Action heroes, Villains, and Main Recap Narrators.
   - Assign 'sreymom' for Female characters, emotional dialogues, romance scenes, and female co-hosts.
5. Output valid JSON list matching the input structure.
"""

SAMPLE_KHMER_RECAP_TEMPLATES = [
    "សាច់រឿងចាប់ផ្ដើមឡើងនៅពេលដែល...",
    "ស្រាប់តែនៅពេលនោះ មានរឿងមិននឹកស្មានដល់មួយបានកើតឡើង...",
    "បន្ទាប់ពីហេតុការណ៍នោះកន្លងផុតទៅ...",
    "តើអ្នកទាំងអស់គ្នាគិតថាតួឯករបស់យើងនឹងដោះស្រាយរឿងនេះយ៉ាងណា?",
    "សូមតាមដានទស្សនាភាគបន្តទាំងអស់គ្នា!"
]


class DramaTranslator:
    def __init__(self, gemini_api_key: Optional[str] = None):
        self.api_key = gemini_api_key or os.environ.get("GEMINI_API_KEY", "")
        self.client = None
        if self.api_key and GENAI_AVAILABLE:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"Warning: Gemini client init error: {e}")

    def set_api_key(self, api_key: str):
        self.api_key = api_key
        if self.api_key and GENAI_AVAILABLE:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"Gemini client setup error: {e}")

    async def translate_text_free(self, text: str, source_lang: str = "auto") -> str:
        """
        Free fallback translation using public Google Translate API endpoint.
        """
        if not text or not text.strip():
            return ""
        
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "gtx",
                "sl": source_lang,
                "tl": "km",
                "dt": "t",
                "q": text
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    translated_parts = [segment[0] for segment in data[0] if segment and segment[0]]
                    return "".join(translated_parts)
        except Exception as e:
            print(f"Free translate error: {e}")

        return text

    def _auto_assign_voice(self, speaker_name: str, text: str, current_voice: Optional[str] = None) -> str:
        """Heuristically assign Piseth (male/narrator) or Sreymom (female) based on speaker name or text context."""
        if current_voice in ("piseth", "sreymom"):
            return current_voice

        name_lower = (speaker_name or "").lower()
        female_keywords = ["female", "woman", "girl", "mother", "sister", "queen", "princess", "lady", "sreymom", "ស្រី", "នាង", "ម៉ាក់", "អ្នកនាង", "ស្ត្រី"]
        male_keywords = ["male", "man", "boy", "father", "brother", "king", "prince", "lord", "piseth", "ប្រុស", "លោក", "ប៉ា", "បងប្រុស", "បុរស", "narrator", "recap"]

        for kw in female_keywords:
            if kw in name_lower:
                return "sreymom"
        for kw in male_keywords:
            if kw in name_lower:
                return "piseth"

        # Check in text
        if any(w in text for w in ["នាង", "អូន", "ស្រី", "ព្រះនាង", "អ្នកនាង"]):
            return "sreymom"
            
        return "piseth"

    async def translate_dialogues(
        self,
        dialogues: List[Dict[str, Any]],
        mode: str = "drama_dubbing",  # 'drama_dubbing' or 'movie_recap'
        source_lang: str = "auto",
        target_voice_override: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Translate a list of dialogue items into Khmer.
        Each item has: id, start, end, text, speaker (optional)
        """
        if not dialogues:
            return []

        # If Gemini AI is active and configured, use it for optimal drama phrasing
        if self.client and self.api_key:
            try:
                prompt = f"""Mode: {mode} (Drama Dubbing vs Facebook Movie Recap)
Source Language: {source_lang}
Input script items in JSON:
{json.dumps(dialogues, ensure_ascii=False, indent=2)}

Translate each dialogue item text into Khmer ('text_km').
Assign 'voice' to either 'piseth' or 'sreymom' for each line.
If mode is 'movie_recap', polish the lines to have a dramatic movie recap storytelling style.
Return ONLY valid JSON array with keys: id, start, end, text_original, text_km, speaker, voice."""

                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=DRAMA_PROMPT_SYSTEM,
                        response_mime_type="application/json"
                    )
                )

                if response.text:
                    parsed = json.loads(response.text)
                    if isinstance(parsed, list):
                        # Merge timing from originals
                        for i, item in enumerate(parsed):
                            if i < len(dialogues):
                                item["start"] = dialogues[i].get("start", item.get("start", 0))
                                item["end"] = dialogues[i].get("end", item.get("end", 0))
                                if target_voice_override:
                                    item["voice"] = target_voice_override
                        return parsed
            except Exception as e:
                print(f"Gemini translation failed, falling back to free engine: {e}")

        # Fallback free translation pipeline
        results = []
        for item in dialogues:
            orig_text = item.get("text") or item.get("text_original", "")
            speaker = item.get("speaker", "Speaker")
            start = item.get("start", 0.0)
            end = item.get("end", 0.0)

            # Translate line
            text_km = await self.translate_text_free(orig_text, source_lang=source_lang)
            
            # Post-process for recap style if requested
            if mode == "movie_recap" and not text_km.startswith(("នៅ", "បន្ទាប់", "ស្រាប់")):
                pass # Can be lightly formatted

            voice = target_voice_override or self._auto_assign_voice(speaker, text_km, item.get("voice"))

            results.append({
                "id": item.get("id", len(results) + 1),
                "start": start,
                "end": end,
                "speaker": speaker,
                "text_original": orig_text,
                "text_km": text_km,
                "voice": voice,
                "rate_percent": item.get("rate_percent", 0),
                "pitch_hz": item.get("pitch_hz", 0)
            })

        return results


def parse_srt_content(srt_text: str) -> List[Dict[str, Any]]:
    """Parse SRT subtitle text into dialogue objects with start/end in seconds."""
    items = []
    # Pattern for SRT blocks
    blocks = re.split(r'\n\s*\n', srt_text.strip())
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            idx = lines[0].strip()
            time_match = re.search(r'(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})', lines[1])
            if time_match:
                h1, m1, s1, ms1, h2, m2, s2, ms2 = [int(x) for x in time_match.groups()]
                start_sec = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000.0
                end_sec = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000.0
                text = " ".join([l.strip() for l in lines[2:] if l.strip()])
                
                # Check for speaker tag like [Speaker]: or Person:
                speaker = "Narrator"
                speaker_match = re.match(r'^\[?([A-Za-z0-9_\u1780-\u17FF\s]+)\]?:\s*(.*)', text)
                if speaker_match:
                    speaker = speaker_match.group(1).strip()
                    text = speaker_match.group(2).strip()

                items.append({
                    "id": idx,
                    "start": round(start_sec, 2),
                    "end": round(end_sec, 2),
                    "speaker": speaker,
                    "text": text,
                    "text_original": text
                })
    return items


def format_srt_content(dialogues: List[Dict[str, Any]], use_km: bool = True) -> str:
    """Export dialogues to standard SRT subtitle string."""
    def _sec_to_srt_time(sec: float) -> str:
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = int(sec % 60)
        ms = int(round((sec - int(sec)) * 1000))
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    lines = []
    for idx, item in enumerate(dialogues, start=1):
        start_str = _sec_to_srt_time(item.get("start", 0))
        end_str = _sec_to_srt_time(item.get("end", 0))
        text = item.get("text_km") if use_km else item.get("text_original", item.get("text", ""))
        lines.append(f"{idx}\n{start_str} --> {end_str}\n{text}\n")

    return "\n".join(lines)
