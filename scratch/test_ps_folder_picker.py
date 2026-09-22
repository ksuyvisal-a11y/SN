import subprocess
import base64
import json
from pathlib import Path

def get_silent_kwargs():
    kwargs = {}
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    return kwargs

def test_file_dialog_json_syntax():
    ps_code = """
Add-Type -AssemblyName System.Windows.Forms
$f = New-Object System.Windows.Forms.OpenFileDialog
$f.Title = 'ជ្រើសរើសវីដេអូរឿងភាគ (Select Drama Videos)'
$f.Filter = 'Video Files (*.mp4;*.mkv;*.mov;*.avi;*.webm;*.flv;*.ts;*.m4v)|*.mp4;*.mkv;*.mov;*.avi;*.webm;*.flv;*.ts;*.m4v|All Files (*.*)|*.*'
$f.Multiselect = $true
$arr = @('D:/test1.mp4', 'D:/test2.mp4')
$json = ConvertTo-Json -Compress $arr
Write-Output ('RESULT:' + $json)
"""
    encoded = base64.b64encode(ps_code.encode("utf-16le")).decode("ascii")
    proc = subprocess.run(
        ["powershell.exe", "-STA", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
        capture_output=True,
        text=True,
        encoding="utf-8",
        **get_silent_kwargs()
    )
    print("STDOUT:", proc.stdout.strip())
    for line in proc.stdout.splitlines():
        if line.startswith("RESULT:"):
            data = json.loads(line[7:].strip())
            print("Parsed data:", data)

test_file_dialog_json_syntax()
