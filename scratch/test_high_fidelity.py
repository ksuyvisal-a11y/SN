import asyncio
import edge_tts
from pathlib import Path
import re
import subprocess
import sys
sys.path.insert(0, ".")
from audio_processor import get_ffmpeg_path

# Monkeypatch communicate to use 96kbitrate for studio quality
file_path = inspect_file = edge_tts.communicate.__file__
with open(file_path, "r", encoding="utf-8") as f:
    orig_code = f.read()

new_code = orig_code.replace(
    '"outputFormat":"audio-24khz-48kbitrate-mono-mp3"',
    '"outputFormat":"audio-24khz-96kbitrate-mono-mp3"'
)
namespace = dict(edge_tts.communicate.__dict__)
exec(compile(new_code, file_path, "exec"), namespace)
CommClass = namespace["Communicate"]

test_sentences = [
    ("piseth", "សួស្តីបងប្អូនទាំងអស់គ្នា។ ថ្ងៃនេះខ្ញុំសូមណែនាំនូវសាច់រឿងភាគពិសេសមួយ ដែលមានភាពជក់ចិត្តដិតអារម្មណ៍ជាខ្លាំង។"),
    ("sreymom", "តើឯងគិតថា ខ្ញុំជាមនុស្សងាយស្រួលនឹងបោកប្រាស់មែនទេ? ឈប់ភ្លាមទៅ ខ្ញុំមិនជឿពាក្យសម្ដីឯងទៀតឡើយ។"),
    ("piseth", "មិនអីទេ កុំបារម្ភអី។ ខ្ញុំនឹងនៅក្បែរអ្នកជានិច្ច មិនឱ្យនរណាម្នាក់មកធ្វើបាបអ្នកបានឡើយ។"),
    ("sreymom", "អរគុណច្រើនហើយលោកប្រធាន ដែលតែងតែជួយយកអាសាខ្ញុំកន្លងមក។")
]

async def run_tests():
    out_dir = Path("scratch/test_studio_voices")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    for i, (voice, text) in enumerate(test_sentences):
        voice_id = "km-KH-PisethNeural" if voice == "piseth" else "km-KH-SreymomNeural"
        c = CommClass(text, voice_id)
        out_raw = out_dir / f"{i+1}_{voice}_raw96k.mp3"
        await c.save(str(out_raw))
        
        # Now apply studio post-processing: 48kHz resample, gentle normalization
        out_studio = out_dir / f"{i+1}_{voice}_speechgen_match.mp3"
        cmd = [
            get_ffmpeg_path(), "-y", "-i", str(out_raw),
            "-ar", "48000",
            "-b:a", "128k",
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            str(out_studio)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Generated {out_studio.name} ({out_studio.stat().st_size} bytes)")

asyncio.run(run_tests())
