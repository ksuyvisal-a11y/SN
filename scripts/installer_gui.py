"""
SN TOOL - Official Modern Frameless Splash Installer & Launcher (v1.0.1)
Displays the 3D Gold Emblem Logo for 3 seconds, sets up in the background,
and immediately transitions straight into the Studio / License Key screen.
"""

import os
import sys
import time
import shutil
import zipfile
import threading
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk

# High DPI awareness
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def get_default_install_dir() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "Programs" / "SN_TOOL"
    return Path.home() / "SN_TOOL"


def create_windows_shortcut(target_exe: Path, shortcut_path: Path, icon_file: Path = None, description: str = "SN TOOL - STUDIO PRO"):
    try:
        ps_cmd = f"""
$ws = New-Object -ComObject WScript.Shell;
$s = $ws.CreateShortcut('{shortcut_path}');
$s.TargetPath = '{target_exe}';
$s.WorkingDirectory = '{target_exe.parent}';
$s.Description = '{description}';
$s.IconLocation = '{icon_file},0';
$s.Save();
"""
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
            capture_output=True,
            creationflags=0x08000000 if sys.platform == "win32" else 0
        )
        return True
    except Exception:
        return False


def get_resource_path(relative_name: str) -> Path:
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        p = Path(sys._MEIPASS) / relative_name
        if p.exists():
            return p
    exe_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent.parent
    for c in [exe_dir / relative_name, exe_dir / "cache" / relative_name, exe_dir / "static" / relative_name, Path(__file__).resolve().parent.parent / relative_name]:
        if c.exists():
            return c
    return Path(relative_name)


class SnToolSplashInstaller:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.overrideredirect(True)  # Frameless modern window
        self.root.configure(bg="#080706")
        
        self.width = 440
        self.height = 490
        
        # Center window on screen
        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        x = (ws - self.width) // 2
        y = (hs - self.height) // 2
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")
        
        # Keep on top initially
        self.root.attributes("-topmost", True)
        
        self.start_time = time.time()
        self.extraction_done = False
        self.progress_val = 0.0
        
        self.logo_img = None
        self._setup_ui()
        
        # Start background extraction
        t = threading.Thread(target=self._run_background_setup, daemon=True)
        t.start()
        
        # Start animation ticker
        self.root.after(40, self._tick_animation)

    def _setup_ui(self):
        # Outer border frame with gold border accent
        outer = tk.Frame(self.root, bg="#080706", highlightbackground="#facc15", highlightcolor="#facc15", highlightthickness=1.5)
        outer.pack(fill="both", expand=True)

        # Inner container
        inner = tk.Frame(outer, bg="#0d0b09", padx=20, pady=24)
        inner.pack(fill="both", expand=True, padx=2, pady=2)

        # 1. 3D Gold Logo
        logo_path = get_resource_path("logo.png")
        if not logo_path.exists():
            logo_path = get_resource_path("static/logo.png")
            
        if logo_path.exists():
            try:
                from PIL import Image, ImageTk
                img = Image.open(str(logo_path)).convert("RGBA")
                img = img.resize((140, 160), Image.Resampling.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(img)
                lbl_logo = tk.Label(inner, image=self.logo_img, bg="#0d0b09")
                lbl_logo.pack(pady=(10, 12))
            except Exception:
                pass

        # 2. Brand Titles
        title_lbl = tk.Label(
            inner,
            text="SN TOOL",
            font=("Segoe UI", 24, "bold"),
            fg="#facc15",
            bg="#0d0b09"
        )
        title_lbl.pack(pady=(0, 2))

        sub_lbl = tk.Label(
            inner,
            text="STUDIO PRO • v1.0.1",
            font=("Segoe UI", 10, "bold"),
            fg="#94a3b8",
            bg="#0d0b09"
        )
        sub_lbl.pack(pady=(0, 20))

        # 3. Status text
        self.status_lbl = tk.Label(
            inner,
            text="កំពុងដំណើរការកម្មវិធី... (Starting Studio...)",
            font=("Segoe UI", 9),
            fg="#cbd5e1",
            bg="#0d0b09"
        )
        self.status_lbl.pack(pady=(0, 10))

        # 4. Sleek Progress Bar
        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "SplashGold.Horizontal.TProgressbar",
            troughcolor="#1c1917",
            background="#facc15",
            thickness=6
        )

        self.prog_bar = ttk.Progressbar(
            inner,
            orient="horizontal",
            length=320,
            mode="determinate",
            style="SplashGold.Horizontal.TProgressbar"
        )
        self.prog_bar.pack(pady=(0, 14))

        # 5. Bottom micro label
        foot_lbl = tk.Label(
            inner,
            text="Khmer AI Drama Voice Translator & Movie Recap Studio",
            font=("Segoe UI", 7),
            fg="#64748b",
            bg="#0d0b09"
        )
        foot_lbl.pack(side="bottom")

    def _run_background_setup(self):
        target_dir = get_default_install_dir()
        payload_zip = get_resource_path("setup_payload.zip")
        if not payload_zip.exists():
            payload_zip = get_resource_path("cache/setup_payload.zip")

        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            
            if payload_zip.exists():
                with zipfile.ZipFile(payload_zip, 'r') as zf:
                    zf.extractall(target_dir)

            # Create Desktop Shortcut
            target_exe = target_dir / "SN_TOOL.exe"
            icon_file = target_dir / "icon.ico"
            if not icon_file.exists():
                src_icon = get_resource_path("icon.ico")
                if src_icon.exists():
                    shutil.copy2(src_icon, icon_file)

            if target_exe.exists():
                desktop = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
                if desktop.exists():
                    create_windows_shortcut(
                        target_exe=target_exe,
                        shortcut_path=desktop / "SN TOOL.lnk",
                        icon_file=icon_file,
                        description="SN TOOL - STUDIO PRO (Khmer AI Drama Studio)"
                    )
                appdata = os.environ.get("APPDATA")
                if appdata:
                    start_programs = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
                    if start_programs.exists():
                        create_windows_shortcut(
                            target_exe=target_exe,
                            shortcut_path=start_programs / "SN TOOL.lnk",
                            icon_file=icon_file,
                            description="SN TOOL - STUDIO PRO"
                        )
        except Exception as e:
            print("Setup exception:", e)
        finally:
            self.extraction_done = True

    def _tick_animation(self):
        elapsed = time.time() - self.start_time
        target_pct = min(100.0, (elapsed / 3.0) * 100.0)

        # Smooth progression
        if self.progress_val < target_pct:
            self.progress_val += (target_pct - self.progress_val) * 0.35
        self.prog_bar["value"] = self.progress_val

        # After 3 full seconds and extraction done, launch app!
        if elapsed >= 3.0 and self.extraction_done:
            self.prog_bar["value"] = 100.0
            self.status_lbl.config(text="✅ រួចរាល់! កំពុងបើកកម្មវិធី...", fg="#4ade80")
            self.root.after(250, self._launch_and_exit)
            return

        self.root.after(35, self._tick_animation)

    def _launch_and_exit(self):
        target_exe = get_default_install_dir() / "SN_TOOL.exe"
        if target_exe.exists():
            subprocess.Popen([str(target_exe)], cwd=str(target_exe.parent))
        self.root.destroy()
        sys.exit(0)


def main():
    root = tk.Tk()
    app = SnToolSplashInstaller(root)
    root.mainloop()


if __name__ == "__main__":
    main()
