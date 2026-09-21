import subprocess
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent.parent))
from audio_processor import get_ffmpeg_path, load_audio_safely

in_wav = "data/projects/2acd4b0b/original_audio.wav"
ffmpeg = get_ffmpeg_path()

# Maximum vocal cancellation filter
filter_max_kill = (
    "pan=stereo|c0=0.5*c0-0.5*c1|c1=0.5*c0-0.5*c1,"
    "equalizer=f=300:t=q:w=1.5:g=-16,"
    "equalizer=f=800:t=q:w=1.5:g=-22,"
    "equalizer=f=1600:t=q:w=1.8:g=-24,"
    "equalizer=f=2500:t=q:w=1.8:g=-24,"
    "equalizer=f=3400:t=q:w=1.5:g=-18"
)

out_test = "scratch/test_max_vocal_kill.wav"
cmd = [ffmpeg, "-y", "-i", in_wav, "-af", filter_max_kill, "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", out_test]
subprocess.run(cmd, check=True)

orig_seg = load_audio_safely(in_wav)
kill_seg = load_audio_safely(out_test)

for idx, (s, e) in enumerate([(0.0, 2.15), (2.2, 3.32), (3.72, 7.76), (8.3, 10.46)]):
    s_ms, e_ms = int(s*1000), int(e*1000)
    o_db = orig_seg[s_ms:e_ms].dBFS
    k_db = kill_seg[s_ms:e_ms].dBFS
    print(f"D#{idx+1} Orig: {o_db:.2f} dBFS, MaxKill: {k_db:.2f} dBFS -> REDUCTION: {o_db - k_db:.2f} dB")
