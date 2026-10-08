import sys
import subprocess
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from audio_processor import get_ffmpeg_path

def generate_sample_lower_thirds():
    ffmpeg = get_ffmpeg_path()
    lt_dir = Path("static/assets/lower_thirds")
    lt_dir.mkdir(parents=True, exist_ok=True)

    # 1. Subscribe/Follow Animated Badge (4s loop)
    sub_p = lt_dir / "subscribe_badge.mp4"
    cmd1 = [
        ffmpeg, "-y",
        "-f", "lavfi", "-i", "color=c=0x111827:s=600x120:d=4",
        "-vf", (
            "drawbox=x=0:y=0:w=600:h=120:color=0x38bdf8@0.9:t=2,"
            "drawbox=x=4:y=4:w=592:h=112:color=0x0f172a@0.95:t=fill,"
            "drawtext=text='FOLLOW AND SHARE':fontsize=26:fontcolor=0xfacc15:x=40:y=30,"
            "drawtext=text='SN DRAMA OFFICIAL':fontsize=22:fontcolor=white:x=40:y=70"
        ),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(sub_p)
    ]
    subprocess.run(cmd1, check=True)
    print("Generated:", sub_p.name)

    # 2. Drama Title Bar (4s loop)
    drama_p = lt_dir / "drama_title_bar.mp4"
    cmd2 = [
        ffmpeg, "-y",
        "-f", "lavfi", "-i", "color=c=0x261204:s=640x110:d=4",
        "-vf", (
            "drawbox=x=0:y=0:w=640:h=110:color=0xf59e0b@0.9:t=2,"
            "drawbox=x=4:y=4:w=632:h=102:color=0x1c120c@0.95:t=fill,"
            "drawtext=text='SN DRAMA VIP SERIES':fontsize=26:fontcolor=0xf59e0b:x=40:y=26,"
            "drawtext=text='KHMER DUBBED EPISODES':fontsize=20:fontcolor=0xfef08a:x=40:y=64"
        ),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(drama_p)
    ]
    subprocess.run(cmd2, check=True)
    print("Generated:", drama_p.name)

    # 3. Like & Share Neon Bar (4s loop)
    like_p = lt_dir / "like_share_bar.mp4"
    cmd3 = [
        ffmpeg, "-y",
        "-f", "lavfi", "-i", "color=c=0x1e0e2e:s=560x100:d=4",
        "-vf", (
            "drawbox=x=0:y=0:w=560:h=100:color=0xc084fc@0.9:t=2,"
            "drawbox=x=4:y=4:w=552:h=92:color=0x150824@0.95:t=fill,"
            "drawtext=text='LIKE AND COMMENT':fontsize=24:fontcolor=0xf43f5e:x=35:y=24,"
            "drawtext=text='THANK YOU FOR WATCHING':fontsize=20:fontcolor=white:x=35:y=58"
        ),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(like_p)
    ]
    subprocess.run(cmd3, check=True)
    print("Generated:", like_p.name)

if __name__ == "__main__":
    generate_sample_lower_thirds()
