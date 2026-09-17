import json
import numpy as np
import subprocess
import io
import wave
import imageio_ffmpeg
from faster_whisper import WhisperModel

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

def get_pitch(start_s, dur_s, audio_file):
    if dur_s <= 0.2:
        return 0
    cmd = [
        ffmpeg_exe, '-ss', str(start_s), '-t', str(dur_s),
        '-i', audio_file, '-vn', '-ac', '1', '-ar', '16000',
        '-f', 'wav', '-'
    ]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    with wave.open(io.BytesIO(p.stdout), 'rb') as wf:
        nframes = wf.getnframes()
        if nframes == 0:
            return 0
        raw = wf.readframes(nframes)
        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
    
    frame_len = 1024
    hop = 512
    pitches = []
    min_lag = int(16000 / 320) # 320 Hz
    max_lag = int(16000 / 80)   # 80 Hz
    
    for i in range(0, len(samples) - frame_len, hop):
        frame = samples[i:i+frame_len]
        frame = frame - np.mean(frame)
        energy = np.sum(frame ** 2)
        if energy < 1e5:
            continue
        corr = np.correlate(frame, frame, mode='full')
        corr = corr[len(corr)//2:]
        if len(corr) <= max_lag:
            continue
        peak_lag = min_lag + np.argmax(corr[min_lag:max_lag])
        if corr[peak_lag] > 0.32 * corr[0]:
            f0 = 16000.0 / peak_lag
            pitches.append(f0)
            
    if pitches:
        return float(np.median(pitches))
    return 0

audio_file = 'data/projects/4b45396e/original_audio.wav'
# Test pitch on first 15 segments of 4b45396e.json
with open('data/projects/4b45396e.json', encoding='utf-8') as f:
    d = json.load(f)

print("Testing acoustic pitch detection & gender assignment on real project dialogues...")
for item in d.get('dialogues', [])[:15]:
    st = item['start']
    dur = round(item['end'] - st, 2)
    p = get_pitch(st, dur, audio_file)
    assigned = "FEMALE" if p >= 165 else ("MALE" if p > 0 else "UNKNOWN")
    print(f"ID {item['id']:2d} [{st:6.2f}-{item['end']:6.2f}] ({dur:4.2f}s) Pitch={p:5.1f}Hz -> {assigned:7s} | OrigVoice: {item.get('voice')}")
