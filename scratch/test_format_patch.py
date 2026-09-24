import asyncio
import edge_tts
import sys
sys.path.insert(0, ".")
import inspect
from audio_processor import get_ffmpeg_path
import subprocess

file_path = inspect.getfile(edge_tts.Communicate)
with open(file_path, "r", encoding="utf-8") as f:
    orig_code = f.read()

for test_fmt in [
    "audio-24khz-96kbitrate-mono-mp3",
    "audio-24khz-160kbitrate-mono-mp3",
    "audio-48khz-96kbitrate-mono-mp3",
    "audio-48khz-192kbitrate-mono-mp3"
]:
    # Replace outputFormat
    new_code = orig_code.replace(
        '"outputFormat":"audio-24khz-48kbitrate-mono-mp3"',
        f'"outputFormat":"{test_fmt}"'
    )

    namespace = dict(edge_tts.communicate.__dict__)
    try:
        exec(compile(new_code, file_path, "exec"), namespace)
        CommClass = namespace["Communicate"]

        async def run_one():
            c = CommClass("សួស្តីបងប្អូនទាំងអស់គ្នា", "km-KH-PisethNeural")
            out_file = f"scratch/test_{test_fmt}.mp3"
            await c.save(out_file)
            return out_file

        res_file = asyncio.run(run_one())
        cmd = [get_ffmpeg_path(), "-i", res_file, "-hide_banner"]
        p = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
        for l in p.stderr.splitlines():
            if "Audio:" in l or "bitrate" in l:
                print(f"SUCCESS {test_fmt}: {l.strip()}")
    except Exception as e:
        print(f"FAILED {test_fmt}: {e}")
