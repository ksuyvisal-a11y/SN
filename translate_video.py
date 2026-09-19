import argparse
import asyncio
import os
import sys
import json
from pathlib import Path

# Enable utf-8 output in Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from pipeline import ProjectManager, SAMPLE_DRAMAS


async def main():
    parser = argparse.ArgumentParser(description="Khmer AI Drama Voice Translator (Piseth & Sreymom)")
    parser.add_argument("--sample", type=str, choices=["chinese_romance", "korean_action", "facebook_recap"],
                        help="Run with pre-built drama sample preset")
    parser.add_argument("--video", type=str, help="Input video file path (MP4/MKV)")
    parser.add_argument("--srt", type=str, help="Input SRT subtitle file path")
    parser.add_argument("--source", type=str, default="auto", choices=["auto", "zh", "ko", "en"],
                        help="Source drama language (Chinese, Korean, English, Auto)")
    parser.add_argument("--mode", type=str, default="drama_dubbing", choices=["drama_dubbing", "movie_recap"],
                        help="Dubbing mode: drama_dubbing or movie_recap (Facebook/TikTok style)")
    parser.add_argument("--voice", type=str, choices=["piseth", "sreymom", "multi", "auto_multi"], default=None,
                        help="Dubbing voice: piseth, sreymom, or multi (Piseth & Sreymom Dual Voice)")
    parser.add_argument("--no-burn", action="store_true", help="Do not burn subtitles into video")

    args = parser.parse_args()
    pm = ProjectManager()

    if args.sample:
        print(f"\n🎬 ដំណើរការគំរូរឿងភាគ: {args.sample}")
        project = pm.load_sample(args.sample)
        print(f"✅ បានបង្កើតគម្រោង: {project['title']}")

        print("\n🎙️ កំពុងបង្កើតសំឡេង ពិសិដ្ឋ & ស្រីមុំ (Batch TTS & Audio Ducking)...")
        project = await pm.generate_project_audio(project["id"])
        print(f"✅ Mixed Audio: {project['mixed_audio_file']}")

        print("\n🎬 កំពុង Render វីដេអូ MP4 ជាមួយ Subtitle ខ្មែរ...")
        project = pm.render_project_video_final(project["id"], burn_subtitles=not args.no_burn)
        print(f"\n🎉 ជោគជ័យ! វីដេអូសម្រេច: {project['output_video_file']}")
        return

    if not args.video and not args.srt:
        print("⚠️ សូមបញ្ជាក់ --sample ឬ --video/--srt")
        parser.print_help()
        return

    if args.video:
        video_p = Path(args.video)
        if not video_p.exists():
            print(f"❌ រកមិនឃើញឯកសារវីដេអូ: {args.video}")
            return

        def cli_progress(pct: int, msg_km: str, msg_en: str):
            print(f"[{pct}%] {msg_km}")

        # Resolve voice: CLI flag or fallback to data/story_config.json
        chosen_voice = args.voice
        if not chosen_voice:
            try:
                cfg_p = Path("data/story_config.json")
                if cfg_p.exists():
                    with open(cfg_p, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                        if cfg.get("auto_multi_voice") or cfg.get("khmer_voice") == "multi":
                            chosen_voice = "multi"
                        else:
                            chosen_voice = cfg.get("khmer_voice", "piseth")
            except Exception:
                chosen_voice = "multi"

        voice_display = "ពិសិដ្ឋ & ស្រីមុំ (Dual Voice)" if chosen_voice in ("multi", "auto_multi") else ("ស្រីមុំ (Sreymom Solo)" if chosen_voice == "sreymom" else "ពិសិដ្ឋ (Piseth Solo)")
        print(f"\n🎬 កំពុងដំណើរការបកប្រែវីដេអូ: {video_p.name} • សំឡេង: {voice_display}")
        project = await pm.process_video_pipeline(
            video_path=str(video_p),
            title=f"Dubbed_{video_p.stem}",
            mode=args.mode,
            source_lang=args.source,
            voice_override=chosen_voice,
            burn_subtitles=not args.no_burn,
            progress_callback=cli_progress
        )

        print("\n========================================================")
        print(f"🎉 បកប្រែ និងបញ្ចូលសំឡេងខ្មែរជោគជ័យ ១០០%!")
        print(f"📁 វីដេអូសម្រេច: {project['output_video_file']}")
        print(f"🎙️ សំឡេងខ្មែរ: {project.get('mixed_audio_file')}")
        print("========================================================\n")
        return


if __name__ == "__main__":
    asyncio.run(main())
