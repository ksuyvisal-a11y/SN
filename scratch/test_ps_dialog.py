import subprocess
import base64
import json
from pathlib import Path

def get_silent_kwargs():
    kwargs = {}
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    return kwargs

def open_native_folder_dialog(initial_dir="D:/"):
    if not initial_dir or not Path(initial_dir).exists():
        initial_dir = "D:/" if Path("D:/").exists() else "C:/"
    initial_dir_esc = str(Path(initial_dir).resolve()).replace("'", "''")

    ps_script = f"""
    [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms") | Out-Null
    $f = New-Object System.Windows.Forms.FolderBrowserDialog
    $f.Description = "ជ្រើសរើស Folder រឿងភាគ (Select Drama Series Folder)"
    $f.ShowNewFolderButton = $false
    if (Test-Path '{initial_dir_esc}') {{
        $f.SelectedPath = '{initial_dir_esc}'
    }}
    $res = $f.ShowDialog()
    if ($res -eq [System.Windows.Forms.DialogResult]::OK) {{
        Write-Output ("RESULT:" + $f.SelectedPath)
    }} else {{
        Write-Output "CANCELLED"
    }}
    """
    encoded = base64.b64encode(ps_script.encode("utf-16le")).decode("ascii")
    cmd = ["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded]
    print("PowerShell command ready:", cmd[:4])
    return True

print("Function defined successfully!")
