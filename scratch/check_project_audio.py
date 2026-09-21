import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from audio_processor import load_audio_safely

p = Path("data/projects/2acd4b0b")
orig = p / "original_audio.wav"
bgm = p / "original_audio_bgm.wav"
mixed = p / "mixed_dubbed_audio.mp3"

for name, path in [("original", orig), ("bgm", bgm), ("mixed", mixed)]:
    if path.exists():
        seg = load_audio_safely(str(path))
        print(f"{name}: dur={len(seg)/1000.0:.2f}s, dBFS={seg.dBFS:.2f}, max_dBFS={seg.max_dBFS:.2f}, channels={seg.channels}")
