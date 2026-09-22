import sys
import os
from pathlib import Path

# Add workspace to path
sys.path.insert(0, r"d:\Sal\SN")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

print("1. Testing imports of upgraded modules...")
try:
    import stt_engine
    import video_processor
    import audio_processor
    import vocal_remover
    import tts_engine
    import pipeline
    print("✅ All modules imported successfully!")
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

print("2. Checking stt_engine functions...")
assert hasattr(stt_engine, "load_audio_samples_16k"), "Missing load_audio_samples_16k"
assert hasattr(stt_engine, "transcribe_audio"), "Missing transcribe_audio"
assert hasattr(stt_engine, "SpeechToTextEngine"), "Missing SpeechToTextEngine"
print("✅ stt_engine functions present!")

print("3. Checking STT engine prompt cleanliness...")
import inspect
stt_src = inspect.getsource(stt_engine.SpeechToTextEngine.transcribe_audio)
assert "李沐谦" not in stt_src, "STT still contains hardcoded character names!"
assert "threshold=0.45" in stt_src, "VAD threshold should be 0.45"
assert "has_pause" in stt_src, "Word-level pause detection missing"
print("✅ STT engine prompt is clean and VAD settings verified!")

print("4. Checking video_processor ffmpeg options...")
import inspect
render_src = inspect.getsource(video_processor.render_dubbed_video)
assert "-nostdin" in render_src, "Missing -nostdin in render_dubbed_video"
assert "scale=trunc(iw/2)*2:trunc(ih/2)*2" in render_src, "Missing odd-dimension fix in render_dubbed_video"
print("✅ video_processor safeguards verified!")

print("5. Checking audio_processor ffmpeg options...")
audio_src = inspect.getsource(audio_processor.enhance_voice_clarity_studio)
assert "-nostdin" in audio_src, "Missing -nostdin in audio_processor"
print("✅ audio_processor safeguards verified!")

print("6. Checking vocal_remover safeguards...")
vocal_src = inspect.getsource(vocal_remover.separate_vocals_and_bgm)
assert "-nostdin" in vocal_src, "Missing -nostdin in vocal_remover"
print("✅ vocal_remover safeguards verified!")

print("7. Checking tts_engine fallback...")
tts_src = inspect.getsource(tts_engine.synthesize_khmer_speech)
assert "silence.export" in tts_src or "wave.open" in tts_src, "Missing fallback audio in tts_engine"
print("✅ tts_engine fallback verified!")

print("\n🎉 ALL UNIT CHECKS PASSED!")
