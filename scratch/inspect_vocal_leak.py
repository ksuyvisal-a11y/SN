import json
import numpy as np
from pathlib import Path
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent.parent))
from audio_processor import load_audio_safely

p = Path("data/projects/2acd4b0b")
with open("data/projects/2acd4b0b.json", "r", encoding="utf-8") as f:
    proj = json.load(f)

orig_audio = load_audio_safely(str(p / "original_audio.wav"))
old_bgm = load_audio_safely(str(p / "original_audio_bgm.wav"))
improved_bgm = load_audio_safely(str(p / "test_improved_bgm.wav"))

dialogues = proj.get("dialogues", [])
print(f"Checking first 5 dialogues:")
for idx, d in enumerate(dialogues[:5]):
    s_ms = int(d["start"] * 1000)
    e_ms = int(d["end"] * 1000)
    orig_chunk = orig_audio[s_ms:e_ms]
    old_chunk = old_bgm[s_ms:e_ms]
    new_chunk = improved_bgm[s_ms:e_ms]
    
    print(f"D#{idx+1} [{d['start']:.2f} - {d['end']:.2f}]")
    print(f"   Orig dBFS: {orig_chunk.dBFS:.2f}")
    print(f"   Old BGM dBFS: {old_chunk.dBFS:.2f} (reduction: {orig_chunk.dBFS - old_chunk.dBFS:.2f} dB)")
    print(f"   New BGM dBFS: {new_chunk.dBFS:.2f} (reduction: {orig_chunk.dBFS - new_chunk.dBFS:.2f} dB)")
