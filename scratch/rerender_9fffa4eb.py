import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from vocal_remover import separate_vocals_and_bgm
from audio_processor import mix_dubbed_audio, create_waveform_data
from video_processor import render_dubbed_video

proj_id = "9fffa4eb"
proj_dir = Path(f"data/projects/{proj_id}")
p_file = Path(f"data/projects/{proj_id}.json")

with open(p_file, "r", encoding="utf-8") as f:
    project = json.load(f)

orig_audio = proj_dir / "original_audio.wav"
dest_video = proj_dir / "source_media.mp4"

print("1. Re-separating BGM with Zero Vocal Leakage cancellation...")
bgm_file, voc_file = separate_vocals_and_bgm(str(orig_audio), output_dir=str(proj_dir))
project["isolated_bgm_file"] = bgm_file
project["isolated_vocals_file"] = voc_file

print("2. Re-mixing audio with Zero Vocal Leakage Dual-Stem Cinema Mixing...")
mixed_audio = proj_dir / "mixed_dubbed_audio.mp3"
dialogues = project.get("dialogues", [])

mix_dubbed_audio(
    original_audio_path=bgm_file,
    dialogue_items=dialogues,
    output_mixed_path=str(mixed_audio),
    total_duration_sec=project.get("duration", 180.0),
    ducking_volume_factor=0.20,
    speech_volume_boost_db=3.5,
    dubbing_mode="smart_bgm"
)
project["mixed_audio_file"] = str(mixed_audio)
project["waveform"] = create_waveform_data(str(mixed_audio))

print("3. Re-rendering final dubbed video...")
output_video_path = proj_dir / "final_dubbed_video.mp4"
render_dubbed_video(
    original_video_path=str(dest_video),
    mixed_audio_path=str(mixed_audio),
    output_video_path=str(output_video_path),
    dialogues=dialogues,
    burn_subtitles=project.get("burn_subtitles", False),
    aspect_ratio=project.get("aspect_ratio", "9:16"),
    temp_dir=str(proj_dir / "temp")
)
project["output_video_file"] = str(output_video_path)

with open(p_file, "w", encoding="utf-8") as f:
    json.dump(project, f, ensure_ascii=False, indent=2)

# Copy to data/exports/ if export exists
exp_dir = Path("data/exports")
for f in exp_dir.glob("*.mp4"):
    if f.stat().st_mtime < (Path(output_video_path).stat().st_mtime + 5):
        pass

print("SUCCESS! Re-render of 9fffa4eb complete!")
