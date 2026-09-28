import sys
import subprocess
import base64
from pathlib import Path

# Let's test a folder picker using PowerShell with System.Windows.Forms.FolderBrowserDialog or OpenFileDialog
ps_code = """
Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.FolderBrowserDialog
$dialog.Description = "Select Drama Folder"
$dialog.ShowNewFolderButton = $false
$form = New-Object System.Windows.Forms.Form
$form.TopMost = $true
$form.StartPosition = [System.Windows.Forms.FormStartPosition]::CenterScreen
$form.ShowInTaskbar = $false
$form.WindowState = [System.Windows.Forms.FormWindowState]::Minimized
$form.Show()
$form.Activate()
$res = $dialog.ShowDialog($form)
if ($res -eq [System.Windows.Forms.DialogResult]::OK) {
    Write-Output ("RESULT:" + $dialog.SelectedPath)
} else {
    Write-Output "CANCELLED"
}
$form.Dispose()
$dialog.Dispose()
"""

print("Testing code...")
