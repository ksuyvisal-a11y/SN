"""
Advanced Subtitle Styler for CapCut/TikTok Style Khmer Captions & Aspect Ratio Framing
"""
from typing import List, Dict, Any

def generate_ass_subtitles(dialogues: List[Dict[str, Any]], style: str = "viral_yellow") -> str:
    """
    Generate Advanced SubStation Alpha (.ass) subtitle format with rich styling
    (Yellow bold text with black border, or cyan glow, or box background).
    """
    # ASS Header
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ViralYellow,Kantumruy Pro,48,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3.5,2,2,40,40,65,1
Style: ViralCyan,Kantumruy Pro,48,&H00FFFF00,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3.5,2,2,40,40,65,1
Style: SreymomPink,Kantumruy Pro,48,&H00B672F4,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3.5,2,2,40,40,65,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    def _sec_to_ass_time(sec: float) -> str:
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = int(sec % 60)
        cs = int(round((sec - int(sec)) * 100))
        return f"{h:01d}:{m:02d}:{s:02d}.{cs:02d}"

    events = []
    for item in dialogues:
        start_str = _sec_to_ass_time(item.get("start", 0.0))
        end_str = _sec_to_ass_time(item.get("end", 3.0))
        text = item.get("text_km") or item.get("text_original", "")
        voice = item.get("voice", "piseth")
        
        style_name = "SreymomPink" if voice == "sreymom" else "ViralYellow"
        speaker = item.get("speaker", "")
        
        events.append(f"Dialogue: 0,{start_str},{end_str},{style_name},{speaker},0,0,0,,{text}")

    return header + "\n".join(events)
