# 🎬 Khmer AI Drama Voice Translator & Movie Recap Studio (PRO V2.0)
### កម្មវិធីបកប្រែ និងបញ្ចូលសំឡេងរឿងភាគ AI កម្រិត Commercial (សំឡេងពិសិដ្ឋ និង ស្រីមុំ)

កម្មវិធីកុំព្យូទ័រ (Desktop App & .EXE) ដ៏ទំនើបកម្រិត **Pro Studio** សម្រាប់បកប្រែសំឡេងរឿងភាគពីភាសា **ចិន (Chinese), កូរ៉េ (Korean), និង អង់គ្លេស (English)** មកជាភាសាខ្មែរ ដោយប្រើសំឡេង AI ផ្លូវការ **ពិសិដ្ឋ (Piseth)** និង **ស្រីមុំ (Sreymom)** ក្នុងទម្រង់ **បញ្ចូលសំឡេងរឿងភាគតាមតួអង្គ (Drama Dubbing)** ឬ **សម្រាយសាច់រឿងបែប Facebook/TikTok (FB Movie Recap)**។

---

## 🌟 មុខងារថ្មីៗដែលបាន Upgrade ក្នុង V2.0 PRO (Key Features)

1. 🎧 **AI Vocal & Background Music (BGM/SFX) Separation:**
   - បំបែកសំឡេងនិយាយដើមចេញពីភ្លេងកំដរ និងសំឡេង Effects (ផ្ទុះ, វាយតប់, ដើរ) ១០០%។
   - រក្សាភ្លេងកំដរដើម និង Sound Effects បានយ៉ាងច្បាស់ល្អឥតខ្ចោះ គ្មានសំឡេងភាសាដើមរំខាន។

2. 🎙️ **Faster-Whisper Auto Speech-to-Text (STT):**
   - គ្រាន់តែដាក់វីដេអូចូល AI នឹងស្តាប់ និងទាញយក Subtitles + Timestamps ស្វ័យប្រវត្តិដោយមិនចាំបាច់មាន File SRT។

3. 🔥 **Viral Facebook/TikTok Movie Recap & Hook Engine:**
   - **Viral Hook Generator:** បន្ថែមឃ្លាបើកឆាកទាក់ទាញ (សេដ្ឋីលាក់មុខ, ស្នេហាកម្សត់, វាយតប់, កំប្លែង) ដូចអ្នកបង្កើតមាតិកាល្បីៗលើ Facebook។
   - **Auto CTA Outros:** បន្ថែមប្រយោគ "Like & Follow សម្រាប់ភាគ ២" ដោយស្វ័យប្រវត្តិ។

4. 🔗 **Online Video Link Downloader (YouTube / TikTok / Douyin / Facebook):**
   - គ្រាន់តែ Paste Link វីដេអូពី YouTube, TikTok, Douyin, Facebook, Bilibili... កម្មវិធីនឹងទាញយកមកធ្វើការស្វ័យប្រវត្តិ។

5. 📱 **Aspect Ratio Converter (9:16 Vertical TikTok vs 16:9 Landscape Facebook):**
   - អាច Render ចេញជាទម្រង់ **9:16 (Reels/TikTok/Shorts)** ដោយមាន Blurred Background និងដាក់ Watermark/Logo ផេករបស់អ្នកស្វ័យប្រវត្តិ។

6. 🎨 **Viral CapCut-Style Subtitle Burn-in:**
   - Subtitle ខ្មែរពណ៌លឿងដិត មានស៊ុមខ្មៅ និង Background Box ងាយស្រួលអានលើទូរស័ព្ទដៃ។

---

## 🚀 របៀបបើកដំណើរការកម្មវិធី (How to Launch)

### 🌟 វិធីទី១៖ បើកតាមរយៈ File `.EXE` (Standalone Desktop App)
អ្នកអាចចុចពីរដង (`Double-click`) លើ File EXE ដើម្បីបើកកម្មវិធីផ្ទាល់តែម្តង៖
```
dist\Khmer_AI_Drama_Studio\Khmer_AI_Drama_Studio.exe
```

### 🌟 វិធីទី២៖ បើកតាមរយៈ 1-Click Launcher Batch File
គ្រាន់តែចុចពីរដង (`Double-click`) លើ File:
```
Khmer_Drama_Studio_Launcher.bat
```

### 🌟 វិធីទី៣៖ បើកតាមរយៈ Python Script
```bash
# ដំណើរការ Desktop App
python desktop_app.py

# ឬដំណើរការ Web Studio
python run_studio.py
```

---

## 📁 រចនាសម្ព័ន្ធឯកសារក្នុងគម្រោង (Project Architecture)
- `dist/Khmer_AI_Drama_Studio/Khmer_AI_Drama_Studio.exe` : **File EXE នៃកម្មវិធី Desktop ពេញលេញ V2.0 Pro**
- `Khmer_Drama_Studio_Launcher.bat` : 1-Click Windows Launcher
- `vocal_remover.py` : Engine បំបែកសំឡេងមនុស្ស និងភ្លេងកំដរ BGM
- `stt_engine.py` : Engine Faster-Whisper AI ចាប់សំឡេងដើម (Speech-to-Text)
- `downloader.py` : Engine ទាញយកវីដេអូតាម Link YouTube/TikTok/Douyin/Facebook
- `recap_engine.py` : Engine បង្កើត Viral Hooks និង Outro សម្រាយរឿង
- `subtitle_styler.py` : Engine បង្កើត CapCut/TikTok Style Subtitles
- `desktop_app.py` : Desktop Window Application Controller
- `build_app.py` : Script បង្កើត Executable (.EXE)
- `server.py` : Backend Web Server & REST API Endpoints
- `tts_engine.py` : Engine បង្កើតសំឡេង ពិសិដ្ឋ & ស្រីមុំ តាម Edge-TTS
- `translator.py` : Engine បកប្រែរឿងភាគ (ចិន/កូរ៉េ/អង់គ្លេស -> ខ្មែរ)
- `audio_processor.py` : Engine Mix សំឡេង & BGM Audio Ducking
- `video_processor.py` : Engine Render វីដេអូ MP4, 9:16 Vertical & Subtitles
- `pipeline.py` : Core Pipeline គ្រប់គ្រងគម្រោង និង Presets
- `static/` :
  - `index.html` : ផ្ទាំង Web Studio UI Dashboard V2.0 Pro
  - `style.css` : Cyber Cinema Dark Theme CSS
  - `app.js` : Client Controller
