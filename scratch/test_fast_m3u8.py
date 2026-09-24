import time
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import subprocess
import sys
sys.path.insert(0, ".")
import audio_processor

def fast_download_m3u8(m3u8_url: str, output_mp4: Path, max_workers: int = 10) -> bool:
    t0 = time.time()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    # 1. Fetch root playlist
    req = urllib.request.Request(m3u8_url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as r:
        content = r.read().decode('utf-8', errors='ignore')

    # If it's a master playlist, fetch the media playlist
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    sub_m3u8_url = None
    for line in lines:
        if not line.startswith('#'):
            sub_m3u8_url = urllib.parse.urljoin(m3u8_url, line)
            break

    if sub_m3u8_url and sub_m3u8_url != m3u8_url and '.m3u8' in sub_m3u8_url:
        req2 = urllib.request.Request(sub_m3u8_url, headers=headers)
        with urllib.request.urlopen(req2, timeout=10) as r2:
            content = r2.read().decode('utf-8', errors='ignore')
        base_for_segments = sub_m3u8_url
    else:
        base_for_segments = m3u8_url

    # 2. Extract segment URLs
    segment_urls = []
    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            seg_full = urllib.parse.urljoin(base_for_segments, line)
            segment_urls.append(seg_full)

    if not segment_urls:
        print("No segments found in M3U8!")
        return False

    print(f"Found {len(segment_urls)} segments. Downloading with {max_workers} threads...")
    temp_dir = output_mp4.parent / f"_temp_segs_{output_mp4.stem}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    def download_segment(idx_url):
        idx, url = idx_url
        seg_file = temp_dir / f"seg_{idx:05d}.ts"
        if seg_file.exists() and seg_file.stat().st_size > 1000:
            return idx, True
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
                if len(data) > 0:
                    with open(seg_file, "wb") as f:
                        f.write(data)
                    return idx, True
        except Exception as e:
            pass
        return idx, False

    # Parallel download
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        results = list(pool.map(download_segment, enumerate(segment_urls)))

    failed_count = sum(1 for idx, ok in results if not ok)
    if failed_count > 0:
        print(f"Warning: {failed_count} segments failed. Retrying failed segments...")
        retry_targets = [(idx, segment_urls[idx]) for idx, ok in results if not ok]
        for it in retry_targets:
            download_segment(it)

    # 3. Concatenate all segments into single MP4 using FFmpeg concat protocol
    list_file = temp_dir / "concat_list.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for idx in range(len(segment_urls)):
            seg_p = temp_dir / f"seg_{idx:05d}.ts"
            if seg_p.exists():
                f.write(f"file '{seg_p.name}'\n")

    ffmpeg_bin = audio_processor.get_ffmpeg_path()
    cmd = [
        ffmpeg_bin, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(list_file.name),
        "-c", "copy",
        "-bsf:a", "aac_adtstoasc",
        "-movflags", "+faststart",
        str(output_mp4.resolve())
    ]
    proc = subprocess.run(cmd, cwd=str(temp_dir), capture_output=True)
    
    # Cleanup temp directory
    try:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    except:
        pass

    if output_mp4.exists() and output_mp4.stat().st_size > 1000000:
        sz_mb = output_mp4.stat().st_size / (1024*1024)
        print(f"SUCCESS: {output_mp4.name} ({sz_mb:.1f} MB) in {time.time()-t0:.2f}s!")
        return True
    return False

test_url = "https://play.modujx17.com/20260920/n8GveYyN/index.m3u8"
out = Path("scratch/test_fast_dl.mp4")
fast_download_m3u8(test_url, out, max_workers=12)
