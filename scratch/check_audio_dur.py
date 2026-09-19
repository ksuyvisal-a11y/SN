import sys
import wave

sys.stdout.reconfigure(encoding='utf-8')
with wave.open('data/projects/5bce584c/original_audio_vocals.wav', 'rb') as wf:
    sr = wf.getframerate()
    frames = wf.getnframes()
    dur = frames / sr
    print(f"Vocals duration: {dur:.2f}s, rate: {sr}")

with wave.open('data/projects/5bce584c/original_audio.wav', 'rb') as wf:
    sr = wf.getframerate()
    frames = wf.getnframes()
    dur = frames / sr
    print(f"Original audio duration: {dur:.2f}s, rate: {sr}")
