"""
SN TOOL - Official Windows Setup Installer GUI (v1.0.1)
Professional 1-Click Installer for Khmer AI Drama Studio
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
from tkinter import ttk, filedialog, messagebox

# High DPI awareness
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
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
        import win32com.client  # try pywin32 if available
        shell = win32com.client.Dispatch("WScript.Shell")
        sc = shell.CreateShortCut(str(shortcut_path))
        sc.Targetpath = str(target_exe)
        sc.WorkingDirectory = str(target_exe.parent)
        sc.Description = description
        if icon_file and icon_file.exists():
            sc.IconLocation = f"{icon_file},0"
        sc.save()
        return True
    except Exception:
        pass

    # Powershell fallback
    try:
        icon_line = f"$s.IconLocation = '{icon_file},0';" if icon_file and icon_file.exists() else ""
        ps_cmd = f"""
$ws = New-Object -ComObject WScript.Shell;
$s = $ws.CreateShortcut('{shortcut_path}');
$s.TargetPath = '{target_exe}';
$s.WorkingDirectory = '{target_exe.parent}';
$s.Description = '{description}';
{icon_line}
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


def get_payload_zip_path() -> Path:
    # 1. Bundled inside PyInstaller _MEIPASS
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        p = Path(sys._MEIPASS) / "setup_payload.zip"
        if p.exists():
            return p
            
    # 2. Next to executable
    exe_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent.parent
    candidates = [
        exe_dir / "setup_payload.zip",
        exe_dir / "cache" / "setup_payload.zip",
        Path(__file__).resolve().parent.parent / "cache" / "setup_payload.zip",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


class SnToolInstallerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("SN TOOL - STUDIO PRO v1.0.1 Setup")
        self.root.geometry("560x470")
        self.root.resizable(False, False)
        self.root.configure(bg="#0c0a09")

        # Center window
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        x = (ws - w) // 2
        y = (hs - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        # Set Icon
        self.icon_path = None
        for cand in [
            Path(__file__).resolve().parent.parent / "icon.ico",
            Path(getattr(sys, '_MEIPASS', '')) / "icon.ico" if getattr(sys, 'frozen', False) else None,
            Path(sys.executable).parent / "icon.ico" if getattr(sys, 'frozen', False) else None
        ]:
            if cand and cand.exists():
                self.icon_path = cand
                try:
                    self.root.iconbitmap(str(cand))
                except Exception:
                    pass
                break

        self.install_dir_var = tk.StringVar(value=str(get_default_install_dir()))
        self.create_desktop_sc_var = tk.BooleanVar(value=True)
        self.create_startmenu_sc_var = tk.BooleanVar(value=True)
        self.launch_after_var = tk.BooleanVar(value=True)

        self.is_installing = False
        self.is_completed = False

        self._setup_ui()

    def _setup_ui(self):
        # 1. Header Frame
        header = tk.Frame(self.root, bg="#171412", height=90, padx=20, pady=14)
        header.pack(fill="x")
        header.pack_propagate(False)

        title_lbl = tk.Label(
            header,
            text="🎬 SN TOOL - STUDIO PRO",
            font=("Segoe UI", 14, "bold"),
            fg="#facc15",
            bg="#171412"
        )
        title_lbl.pack(anchor="w")

        sub_lbl = tk.Label(
            header,
            text="កម្មវិធីដំឡើងស្វ័យប្រវត្តិកំណែទម្រង់ Version 1.0.1 (Official Setup Wizard)",
            font=("Segoe UI", 9),
            fg="#94a3b8",
            bg="#171412"
        )
        sub_lbl.pack(anchor="w", pady=(3, 0))

        # Divider line
        div = tk.Frame(self.root, bg="#facc15", height=2)
        div.pack(fill="x")

        # 2. Main Content Frame
        content = tk.Frame(self.root, bg="#0c0a09", padx=24, pady=16)
        content.pack(fill="both", expand=True)

        # Welcome text
        desc_lbl = tk.Label(
            content,
            text="សូមស្វាគមន៍មកកាន់ការដំឡើង SN TOOL (Khmer AI Drama Studio)។\nកម្មវិធីនឹងត្រូវដំឡើងដោយស្វ័យប្រវត្តិលើកុំព្យូទ័ររបស់អ្នកក្នុងរយៈពេលខ្លី។",
            font=("Segoe UI", 9),
            fg="#e2e8f0",
            bg="#0c0a09",
            justify="left"
        )
        desc_lbl.pack(anchor="w", pady=(0, 14))

        # Destination Selection
        dest_lbl = tk.Label(
            content,
            text="ទីតាំងដំឡើង (Install Destination Folder):",
            font=("Segoe UI", 9, "bold"),
            fg="#facc15",
            bg="#0c0a09"
        )
        dest_lbl.pack(anchor="w", pady=(0, 4))

        dest_row = tk.Frame(content, bg="#0c0a09")
        dest_row.pack(fill="x", pady=(0, 10))

        self.dest_entry = tk.Entry(
            dest_row,
            textvariable=self.install_dir_var,
            font=("Segoe UI", 9),
            bg="#1c1917",
            fg="#ffffff",
            insertbackground="#facc15",
            relief="solid",
            bd=1
        )
        self.dest_entry.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 8))

        self.btn_browse = tk.Button(
            dest_row,
            text="Browse...",
            font=("Segoe UI", 9),
            bg="#292524",
            fg="#e2e8f0",
            activebackground="#44403c",
            activeforeground="#ffffff",
            relief="flat",
            padx=12,
            pady=3,
            command=self._on_browse
        )
        self.btn_browse.pack(side="right")

        # Options checkbuttons
        opts_frame = tk.Frame(content, bg="#0c0a09")
        opts_frame.pack(fill="x", pady=(0, 12))

        cb_desktop = tk.Checkbutton(
            opts_frame,
            text="បង្កើតផ្លូវកាត់លើ Desktop (Create Desktop Shortcut)",
            variable=self.create_desktop_sc_var,
            font=("Segoe UI", 9),
            fg="#cbd5e1",
            bg="#0c0a09",
            activebackground="#0c0a09",
            activeforeground="#facc15",
            selectcolor="#1c1917"
        )
        cb_desktop.pack(anchor="w")

        cb_launch = tk.Checkbutton(
            opts_frame,
            text="បើកដំណើរការ SN TOOL ភ្លាមៗក្រោយដំឡើងរួច (Launch SN TOOL now)",
            variable=self.launch_after_var,
            font=("Segoe UI", 9),
            fg="#cbd5e1",
            bg="#0c0a09",
            activebackground="#0c0a09",
            activeforeground="#facc15",
            selectcolor="#1c1917"
        )
        cb_launch.pack(anchor="w")

        # Progress Section
        self.prog_frame = tk.Frame(content, bg="#0c0a09")
        self.prog_frame.pack(fill="x", pady=(6, 0))

        self.status_lbl = tk.Label(
            self.prog_frame,
            text="ត្រៀមដំឡើង (Ready to install)",
            font=("Segoe UI", 8),
            fg="#94a3b8",
            bg="#0c0a09"
        )
        self.status_lbl.pack(anchor="w", pady=(0, 4))

        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "Gold.Horizontal.TProgressbar",
            troughcolor="#1c1917",
            background="#facc15",
            thickness=10
        )

        self.prog_bar = ttk.Progressbar(
            self.prog_frame,
            orient="horizontal",
            length=100,
            mode="determinate",
            style="Gold.Horizontal.TProgressbar"
        )
        self.prog_bar.pack(fill="x")

        # 3. Footer Bar
        footer = tk.Frame(self.root, bg="#171412", height=60, padx=20, pady=12)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        self.btn_cancel = tk.Button(
            footer,
            text="Cancel (បោះបង់)",
            font=("Segoe UI", 9),
            bg="#292524",
            fg="#94a3b8",
            activebackground="#44403c",
            activeforeground="#ffffff",
            relief="flat",
            padx=14,
            pady=4,
            command=self._on_cancel
        )
        self.btn_cancel.pack(side="left")

        self.btn_action = tk.Button(
            footer,
            text="ដំឡើងឥឡូវនេះ (Install Now)",
            font=("Segoe UI", 9, "bold"),
            bg="#facc15",
            fg="#0f0d0b",
            activebackground="#eab308",
            activeforeground="#000000",
            relief="flat",
            padx=20,
            pady=4,
            cursor="hand2",
            command=self._on_action_click
        )
        self.btn_action.pack(side="right")

    def _on_browse(self):
        chosen = filedialog.askdirectory(initialdir=self.install_dir_var.get(), title="ជ្រើសរើស Folder ដំឡើង SN TOOL")
        if chosen:
            self.install_dir_var.set(chosen)

    def _on_cancel(self):
        if self.is_installing:
            if not messagebox.askyesno("បញ្ជាក់", "តើអ្នកពិតជាចង់បោះបង់ការដំឡើងមែនទេ?"):
                return
        self.root.destroy()

    def _on_action_click(self):
        if self.is_completed:
            # Finish action
            if self.launch_after_var.get():
                target_exe = Path(self.install_dir_var.get()) / "SN_TOOL.exe"
                if target_exe.exists():
                    subprocess.Popen([str(target_exe)], cwd=str(target_exe.parent))
            self.root.destroy()
            return

        if self.is_installing:
            return

        # Start installation in thread
        self.is_installing = True
        self.dest_entry.config(state="disabled")
        self.btn_browse.config(state="disabled")
        self.btn_action.config(state="disabled", text="កំពុងដំឡើង... (Installing)")
        self.btn_cancel.config(state="disabled")

        t = threading.Thread(target=self._run_install_thread, daemon=True)
        t.start()

    def _run_install_thread(self):
        target_dir = Path(self.install_dir_var.get())
        payload_zip = get_payload_zip_path()

        if not payload_zip.exists():
            self._set_status(f"Error: រកមិនឃើញកញ្ចប់ដំឡើង ({payload_zip.name})", error=True)
            self._enable_action("បរាជ័យ (Failed)")
            return

        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            
            self._set_status("កំពុងពិនិត្យ និងពន្លាឯកសារ... (Reading package)")
            with zipfile.ZipFile(payload_zip, 'r') as zf:
                file_list = [f for f in zf.infolist() if not f.is_dir()]
                total_files = len(file_list)
                
                for idx, item in enumerate(file_list):
                    # Extract single file
                    dest_f = target_dir / item.filename
                    dest_f.parent.mkdir(parents=True, exist_ok=True)
                    
                    try:
                        zf.extract(item, target_dir)
                    except Exception:
                        pass
                        
                    # Update progress every 15 files
                    if idx % 15 == 0 or idx == total_files - 1:
                        pct = int(((idx + 1) / total_files) * 90)
                        self._set_progress(pct)
                        fname_short = Path(item.filename).name
                        if len(fname_short) > 28:
                            fname_short = fname_short[:25] + "..."
                        self._set_status(f"កំពុងដំឡើង ({pct}%): {fname_short}")

            # Create Shortcuts
            self._set_progress(95)
            self._set_status("កំពុងបង្កើតផ្លូវកាត់លើ Desktop (Creating Shortcuts)...")
            
            target_exe = target_dir / "SN_TOOL.exe"
            target_icon = target_dir / "icon.ico"
            if not target_icon.exists() and self.icon_path and self.icon_path.exists():
                shutil.copy2(self.icon_path, target_icon)

            if self.create_desktop_sc_var.get() and target_exe.exists():
                desktop = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
                if desktop.exists():
                    create_windows_shortcut(
                        target_exe=target_exe,
                        shortcut_path=desktop / "SN TOOL.lnk",
                        icon_file=target_icon,
                        description="SN TOOL - STUDIO PRO (Khmer AI Drama Studio)"
                    )

            if self.create_startmenu_sc_var.get() and target_exe.exists():
                appdata = os.environ.get("APPDATA")
                if appdata:
                    start_programs = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
                    if start_programs.exists():
                        create_windows_shortcut(
                            target_exe=target_exe,
                            shortcut_path=start_programs / "SN TOOL.lnk",
                            icon_file=target_icon,
                            description="SN TOOL - STUDIO PRO"
                        )

            # Success
            self._set_progress(100)
            self._set_status("✅ ដំឡើងជោគជ័យ ១០០% (Installation Completed!)")
            self.is_completed = True
            self._enable_action("បញ្ចប់ (Finish)", success=True)

        except Exception as e:
            self._set_status(f"Error: {e}", error=True)
            self._enable_action("បរាជ័យ (Failed)")

    def _set_status(self, text: str, error: bool = False):
        fg = "#ef4444" if error else ("#4ade80" if "ជោគជ័យ" in text else "#94a3b8")
        self.root.after(0, lambda: self.status_lbl.config(text=text, fg=fg))

    def _set_progress(self, val: int):
        self.root.after(0, lambda: self.prog_bar.config(value=val))

    def _enable_action(self, btn_text: str, success: bool = False):
        def _cb():
            self.btn_action.config(state="normal", text=btn_text)
            if success:
                self.btn_action.config(bg="#22c55e", fg="#ffffff")
                self.btn_cancel.config(state="disabled")
            else:
                self.btn_cancel.config(state="normal")
        self.root.after(0, _cb)


def main():
    root = tk.Tk()
    app = SnToolInstallerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
