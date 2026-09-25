import urllib.request
import urllib.parse
import re
import os
import shutil
import tempfile
import concurrent.futures
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def download_hls_stream_pool(m3u8_url: str, dest_file: Path, max_workers: int = 16, timeout_sec: int = 15) -> bool:
    """
    High-speed multi-threaded HLS TS fragment downloader.
    Downloads all segments in parallel and transmuxes cleanly with FFmpeg stream copy.
    """
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries, pool_connections=max_workers, pool_maxsize=max_workers)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

    # 1. Fetch root M3U8
    try:
        r = session.get(m3u8_url, timeout=10)
        r.raise_for_status()
        m3u8_content = r.text
    except Exception as e:
        print("Root M3U8 fetch failed:", e)
        return False

    # 2. Check for Master Playlist
    current_url = m3u8_url
    if '#EXT-X-STREAM-INF' in m3u8_content:
        sub_url = None
        for line in m3u8_content.splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                sub_url = urllib.parse.urljoin(m3u8_url, line)
                break
        if sub_url:
            current_url = sub_url
            try:
                r2 = session.get(sub_url, timeout=10)
                r2.raise_for_status()
                m3u8_content = r2.text
            except Exception as e:
                print("Sub M3U8 fetch failed:", e)
                return False

    # 3. Extract all TS segment URLs
    segment_urls = []
    for line in m3u8_content.splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            seg_full = urllib.parse.urljoin(current_url, line)
            segment_urls.append(seg_full)

    if not segment_urls:
        print("No segments found in M3U8")
        return False

    print(f"Extracted {len(segment_urls)} segments to download...")

    # 4. Download segments in parallel
    temp_dir = Path(tempfile.mkdtemp(prefix="hls_turbo_"))
    try:
        def download_seg(args):
            idx, url = args
            seg_p = temp_dir / f"seg_{idx:05d}.ts"
            for attempt in range(4):
                try:
                    res = session.get(url, timeout=timeout_sec)
                    if res.status_code == 200 and len(res.content) > 100:
                        with open(seg_p, "wb") as f:
                            f.write(res.content)
                        return True
                except Exception:
                    pass
            return False

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
            results = list(pool.map(download_seg, enumerate(segment_urls)))

        success_count = sum(1 for x in results if x)
        print(f"Downloaded {success_count}/{len(segment_urls)} segments successfully.")
        if success_count < len(segment_urls) * 0.9:
            return False

        # 5. Concatenate all segments into single TS or MP4 via FFmpeg stream copy
        concat_txt = temp_dir / "concat.txt"
        with open(concat_txt, "w", encoding="utf-8") as f:
            for idx in range(len(segment_urls)):
                seg_p = temp_dir / f"seg_{idx:05d}.ts"
                if seg_p.exists() and seg_p.stat().st_size > 0:
                    f.write(f"file '{str(seg_p.resolve()).replace(chr(92), '/')}'\n")

        # Import FFmpeg path
        from audio_processor import get_ffmpeg_path, get_silent_kwargs
        cmd = [
            get_ffmpeg_path(),
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_txt),
            "-c", "copy",
            "-bsf:a", "aac_adtstoasc",
            "-movflags", "+faststart",
            str(dest_file)
        ]
        import subprocess
        subprocess.run(cmd, capture_output=True, timeout=120, **get_silent_kwargs())

        if dest_file.exists() and dest_file.stat().st_size > 1000000:
            print("Successfully assembled into:", dest_file, f"Size: {dest_file.stat().st_size / (1024*1024):.2f} MB")
            return True
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == '__main__':
    url = 'https://play.modujx17.com/20260903/TTKt7izl/index.m3u8'
    dest = Path('scratch/pool_test.mp4')
    if dest.exists(): dest.unlink()
    success = download_hls_stream_pool(url, dest, max_workers=16)
    print("Result:", success)
    if dest.exists(): dest.unlink()
