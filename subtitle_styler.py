"""
Advanced Subtitle Styler for CapCut/TikTok Style Khmer Captions & Aspect Ratio Framing
"""
from typing import List, Dict, Any

def generate_ass_subtitles(
    dialogues: List[Dict[str, Any]], 
    style: str = "viral_yellow", 
    fontsize: int = 48,
    margin_v: int = 65,
    play_res_x: int = 1080,
    play_res_y: int = 1920,
    pos_x: int = None,
    pos_y: int = None,
    animation: str = "pop"
) -> str:
    """
    Generate Advanced SubStation Alpha (.ass) subtitle format with rich styling
    and CapCut/TikTok viral entrance animations (Pop-up Bounce, Smooth Fade In, Slide Up, Classic Static).
    Supports exact pixel-level (pos_x, pos_y) coordinate positioning for faithful video exports.
    """
    fs = max(24, min(100, int(fontsize)))
    mv = max(20, min(play_res_y - 40, int(margin_v)))

    if pos_x is None:
        pos_x = play_res_x // 2
    if pos_y is None:
        pos_y = play_res_y - mv

    # Outline width scaled proportionally
    outline_w = max(2.5, round(fs * 0.08, 1))

    # ASS Header with all available viral styles
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {play_res_x}
PlayResY: {play_res_y}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ViralYellow,Kantumruy Pro,{fs},&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,{outline_w},2,2,40,40,{mv},1
Style: ViralCyan,Kantumruy Pro,{fs},&H00FFFF00,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,{outline_w},2,2,40,40,{mv},1
Style: SreymomPink,Kantumruy Pro,{fs},&H00B672F4,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,{outline_w},2,2,40,40,{mv},1
Style: ClassicWhite,Kantumruy Pro,{fs},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,{outline_w},2,2,40,40,{mv},1
Style: ObsidianBox,Kantumruy Pro,{fs},&H0000FFFF,&H000000FF,&H00000000,&HA0000000,-1,0,0,0,100,100,0,0,3,6,0,2,40,40,{mv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    def _sec_to_ass_time(sec: float) -> str:
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = int(sec % 60)
        cs = int(round((sec - int(sec)) * 100))
        return f"{h:01d}:{m:02d}:{s:02d}.{cs:02d}"

    style_map = {
        "viral_yellow": "ViralYellow",
        "viral_cyan": "ViralCyan",
        "sreymom_pink": "SreymomPink",
        "classic_white": "ClassicWhite",
        "obsidian_box": "ObsidianBox"
    }
    default_style_name = style_map.get(str(style).lower(), "ViralYellow")

    # Determine animation mode: pop, fade, slide, static
    anim_clean = str(animation or "pop").lower().strip()

    events = []
    for item in dialogues:
        start_str = _sec_to_ass_time(item.get("start", 0.0))
        end_str = _sec_to_ass_time(item.get("end", 3.0))
        text = item.get("text_km") or item.get("text_original", "")
        clean_text = str(text).replace("\r\n", "\\N").replace("\n", "\\N")
        voice = item.get("voice", "piseth")
        
        # If user explicitly picked a style (other than auto voice mapping), respect chosen style
        if style and style in style_map:
            style_name = default_style_name
        else:
            style_name = "SreymomPink" if voice == "sreymom" else "ViralYellow"
            
        speaker = item.get("speaker", "")

        # CapCut & TikTok Subtitle Entrance Animations:
        if anim_clean == "pop":
            # Snappy Zoom Pop: scales 118% on speech entrance then snaps to 100% in 180ms
            anim_tag = f"{{\\an2\\pos({pos_x},{pos_y})\\t(0,90,\\fscx118\\fscy118)\\t(90,180,\\fscx100\\fscy100)}}"
        elif anim_clean == "fade":
            # Smooth Dissolve: fades in over 160ms, fades out over 120ms
            anim_tag = f"{{\\an2\\pos({pos_x},{pos_y})\\fad(160,120)}}"
        elif anim_clean == "slide":
            # Slide Up: glides up 22px from below into resting pos_y with light fade
            slide_start_y = min(play_res_y - 10, pos_y + 22)
            anim_tag = f"{{\\an2\\move({pos_x},{slide_start_y},{pos_x},{pos_y},0,180)\\fad(100,80)}}"
        else:  # "static"
            # Instant Crisp Display without motion
            anim_tag = f"{{\\an2\\pos({pos_x},{pos_y})}}"

        events.append(f"Dialogue: 0,{start_str},{end_str},{style_name},{speaker},0,0,0,,{anim_tag}{clean_text}")

    return header + "\n".join(events)
