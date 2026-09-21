import asyncio
import json
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).parent.parent))
from pipeline import ProjectManager

async def run_dub():
    pm = ProjectManager()
    print("Step 1: Generating project audio (batch synthesis + mixing)...")
    proj = await pm.generate_project_audio("84995c0c")
    print(f"Audio generated: {proj.get('mixed_audio_file')}")
    
    print("Step 2: Rendering final video...")
    rendered = pm.render_project_video_final("84995c0c")
    print(f"Final video rendered: {rendered.get('output_video_file')}")

if __name__ == "__main__":
    asyncio.run(run_dub())
