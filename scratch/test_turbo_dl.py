import time
import os
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from audio_processor import get_ffmpeg_path
import yt_dlp

def test_turbo_download(stream_url: str, output_path: str):
    ffmpeg_bin = get_ffmpeg_path()
    opts = {
        'outtmpl': output_path,
        'concurrent_fragment_downloads': 16,
        'retries': 15,
        'fragment_retries': 15,
        'buffersize': 1024 * 1024,
        'http_chunk_size': 10485760,
        'ffmpeg_location': ffmpeg_bin,
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
    }
    t0 = time.time()
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([stream_url])
    t1 = time.time()
    
    out_f = Path(output_path)
    if not out_f.exists():
        # Check if ext was changed
        cand = list(out_f.parent.glob(f"{out_f.stem}.*"))
        if cand:
            out_f = cand[0]
            
    if out_f.exists():
        sz_mb = out_f.stat().st_size / (1024 * 1024)
        print(f"SUCCESS! Downloaded {out_f.name} ({sz_mb:.2f} MB) in {t1-t0:.2f}s! Speed: {sz_mb/(t1-t0):.2f} MB/s")
    else:
        print("FAILED: Output file not created.")

if __name__ == '__main__':
    url = 'https://play.modujx17.com/20260903/TTKt7izl/index.m3u8'
    test_turbo_download(url, 'scratch/turbo_test.mp4')
