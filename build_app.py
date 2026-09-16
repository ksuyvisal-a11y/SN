import os
import sys
import shutil
import subprocess
from pathlib import Path

# Enable utf-8 output in Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def build_exe():
    print("========================================================")
    print(" 🔨 កំពុងចាប់ផ្តើមបង្កើត Executable (.EXE) ជាមួយ License & Admin Tools...")
    print("========================================================")

    base_dir = Path(__file__).resolve().parent
    dist_dir = base_dir / "dist"
    icon_path = base_dir / "icon.ico"

    # Find imageio_ffmpeg binary path to bundle into EXE
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_dir = os.path.dirname(ffmpeg_exe)
        has_ffmpeg = True
    except Exception as e:
        ffmpeg_dir = ""
        has_ffmpeg = False
        print(f"Warning finding ffmpeg: {e}")

    # Build PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=Khmer_AI_Drama_Studio",
        "--onedir",
        "--noconfirm",
        "--clean",
        f"--icon={icon_path}",
        f"--add-data={base_dir / 'static'};static",
    ]

    if has_ffmpeg and ffmpeg_dir:
        cmd.append(f"--add-data={ffmpeg_dir};imageio_ffmpeg/binaries")

    # Add hidden imports
    hidden_imports = [
        "edge_tts",
        "pydub",
        "flask",
        "jinja2",
        "soundfile",
        "httpx",
        "webview",
        "clr_loader",
        "pythonnet"
    ]
    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])

    cmd.append(str(base_dir / "desktop_app.py"))

    print("\nRunning PyInstaller command:")
    print(" ".join(cmd))
    print("\nProcessing... This may take 1-2 minutes...")

    proc = subprocess.run(cmd, cwd=str(base_dir))
    if proc.returncode == 0:
        target_folder = dist_dir / "Khmer_AI_Drama_Studio"
        exe_path = target_folder / "Khmer_AI_Drama_Studio.exe"
        
        # Copy logo assets & admin tools directly into the EXE folder
        files_to_copy = [
            ("static/logo.png", "SN_Logo.png"),
            ("icon.ico", "SN_Logo.ico"),
            ("license.key", "license.key"),
            ("admin_key_history.json", "admin_key_history.json"),
            ("generated_keys_log.txt", "generated_keys_log.txt"),
            ("ADMIN_KEY_GENERATOR.py", "ADMIN_KEY_GENERATOR.py"),
            ("ADMIN_KEY_GENERATOR_LAUNCHER.bat", "ADMIN_KEY_GENERATOR_LAUNCHER.bat"),
            ("license_engine.py", "license_engine.py"),
            ("update.py", "update.py"),
            ("SN_TOOL.bat", "SN_TOOL.bat")
        ]

        for src_name, dst_name in files_to_copy:
            src_file = base_dir / src_name
            if src_file.exists():
                try:
                    shutil.copy2(str(src_file), str(target_folder / dst_name))
                except Exception as e:
                    print(f"Notice copying {src_name}: {e}")

        print(f"\n========================================================")
        print(f" 🎉 បង្កើត .EXE ជាមួយ Admin License System ជោគជ័យ ១០០%!")
        print(f" 📂 ទីតាំង Folder កម្មវិធី: {target_folder}")
        print(f"========================================================\n")
    else:
        print("\n❌ ការបង្កើត .EXE មានបញ្ហា។ សូមពិនិត្យមើល Error ខាងលើ។")

if __name__ == "__main__":
    build_exe()
