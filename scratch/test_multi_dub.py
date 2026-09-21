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

async def test_trans():
    pm = ProjectManager()
    proj = await pm.translate_project("84995c0c", voice_override="multi")
    dialogues = proj.get("dialogues", [])
    voices = {}
    for d in dialogues:
        v = d.get("voice")
        voices[v] = voices.get(v, 0) + 1
    print("Voices breakdown:", voices)
    for i, d in enumerate(dialogues[:8]):
        print(f"#{i+1} [{d.get('voice')}] {d.get('speaker')}: {d.get('text_km')}")

if __name__ == "__main__":
    asyncio.run(test_trans())
