import json
import numpy as np
import subprocess
import io
import wave
import imageio_ffmpeg

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

def get_pitch(start_s, dur_s, audio_file):
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
    min_lag = int(16000 / 320) # ~50 (320 Hz)
    max_lag = int(16000 / 80)   # ~200 (80 Hz)
    
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
        if corr[peak_lag] > 0.30 * corr[0]:
            f0 = 16000.0 / peak_lag
            pitches.append(f0)
            
    if pitches:
        return float(np.median(pitches))
    return 0

test_file = 'data/projects/4b45396e/original_audio.wav'
with open('data/projects/4b45396e.json', encoding='utf-8') as f:
    d = json.load(f)

for item in d.get('dialogues', [])[3:15]:
    st = item['start']
    dur = item['end'] - st
    p = get_pitch(st, dur, test_file)
    gender = 'FEMALE (Sreymom)' if p >= 165 else ('MALE (Piseth)' if p > 0 else 'UNCERTAIN')
    cur_spk = item.get('voice', '')
    print(f"Line {item['id']} [{st:.2f}-{item['end']:.2f}] Pitch: {p:.1f}Hz -> {gender} | CurVoice: {cur_spk}")
