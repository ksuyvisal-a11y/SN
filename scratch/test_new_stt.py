import json
import numpy as np
import subprocess
import io
import wave
import imageio_ffmpeg
from faster_whisper import WhisperModel

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

def detect_segment_pitch(audio_path: str, start_s: float, end_s: float) -> float:
    dur_s = end_s - start_s
    if dur_s <= 0.25:
        return 0.0
    cmd = [
        ffmpeg_exe, '-ss', str(start_s), '-t', str(dur_s),
        '-i', audio_path, '-vn', '-ac', '1', '-ar', '16000',
        '-f', 'wav', '-'
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        with wave.open(io.BytesIO(proc.stdout), 'rb') as wf:
            nframes = wf.getnframes()
            if nframes == 0:
                return 0.0
            raw = wf.readframes(nframes)
            samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
    except Exception:
        return 0.0

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
    return 0.0

audio_path = 'data/projects/4b45396e/original_audio.wav'
# Test transcribe first 60 seconds
model = WhisperModel('base', device='cpu', compute_type='int8')
segments_gen, _ = model.transcribe(
    audio_path,
    language='zh',
    beam_size=3,
    vad_filter=True,
    vad_parameters=dict(min_silence_duration_ms=650, speech_pad_ms=250)
)

raw_segments = []
for s in segments_gen:
    if s.start > 65.0:
        break
    raw_segments.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()})

print(f"Whisper produced {len(raw_segments)} segments for first 60s.")

# Pass 1: acoustic pitch + text cues
speaker_segments = []
current_speaker = "តួប្រុស (ពិសិដ្ឋ)"
for seg in raw_segments:
    st = seg["start"]
    en = seg["end"]
    txt = seg["text"]
    pitch = detect_segment_pitch(audio_path, st, en)
    
    # Text gender hints
    female_kw = any(k in txt for k in ["妈", "母亲", "夫人", "太太", "阿姨", "姑娘", "妹", "姐", "女儿", "丫头", "她", "老板娘", "我老公"])
    male_kw = any(k in txt for k in ["爸", "父亲", "老爷", "老头", "哥", "弟", "男人", "兄弟", "他", "我老婆", "执法官"])
    
    if pitch >= 165.0 or (pitch == 0.0 and female_kw and not male_kw):
        role = "female"
        speaker = "តួស្រី (ស្រីមុំ)"
    elif (0.0 < pitch < 165.0) or (pitch == 0.0 and male_kw and not female_kw):
        role = "male"
        speaker = "តួប្រុស (ពិសិដ្ឋ)"
    else:
        speaker = current_speaker
        role = "female" if "ស្រី" in speaker else "male"
        
    current_speaker = speaker
    speaker_segments.append({
        "start": st, "end": en, "text": txt,
        "speaker": speaker, "pitch": round(pitch, 1), "role": role
    })

# Pass 2: merge same speaker segments
consolidated = []
for seg in speaker_segments:
    if consolidated:
        prev = consolidated[-1]
        gap = round(seg["start"] - prev["end"], 2)
        comb_len = round(seg["end"] - prev["start"], 2)
        same_spk = (prev["role"] == seg["role"])
        
        is_short = (seg["end"] - seg["start"] < 1.4) or (len(seg["text"]) <= 4)
        prev_is_short = (prev["end"] - prev["start"] < 1.4)
        
        if same_spk and comb_len <= 7.5 and (gap <= 0.85 or (is_short and gap <= 1.2) or (prev_is_short and gap <= 1.0)):
            prev["end"] = seg["end"]
            prev["text"] = f"{prev['text']} {seg['text']}".strip()
            continue
            
    consolidated.append(dict(seg))

print(f"Consolidated into {len(consolidated)} clean dialogue turns.")
with open('scratch_new_stt_out.txt', 'w', encoding='utf-8') as out:
    for idx, item in enumerate(consolidated, 1):
        dur = round(item['end'] - item['start'], 2)
        out.write(f"[{idx:2d}] {item['start']:5.2f}s -> {item['end']:5.2f}s ({dur:4.2f}s) | {item['speaker']} (Pitch={item['pitch']}Hz)\n")
        out.write(f"     ZH: {item['text']}\n\n")

print("Done writing scratch_new_stt_out.txt")
