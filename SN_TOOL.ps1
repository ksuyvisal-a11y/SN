# ==============================================================================
# SN TOOL - STUDIO PRO (Khmer AI Drama Studio) - PowerShell Launcher
# ==============================================================================
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$Host.UI.RawUI.WindowTitle = "🎬 SN TOOL - STUDIO PRO (Khmer AI Drama Studio)"

Write-Host "========================================================================" -ForegroundColor Yellow
Write-Host " 🎬 SN TOOL - STUDIO PRO (Native Desktop Application)..." -ForegroundColor Cyan
Write-Host " 🎙️ Khmer Neural Voices: Piseth & Sreymom (SpeechGen.io Quality)" -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Yellow
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($ScriptDir) {
    Set-Location -LiteralPath $ScriptDir
}

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $pythonCmd) {
    $pythonCmd = Get-Command py -ErrorAction SilentlyContinue
}

if ($pythonCmd) {
    if (Test-Path "desktop_app.py") {
        Write-Host "🖥️ Starting Native Desktop Window (desktop_app.py)..." -ForegroundColor Cyan
        & $pythonCmd.Source "desktop_app.py"
        exit 0
    } elseif (Test-Path "run_studio.py") {
        Write-Host "🌐 Starting Studio Web Server (run_studio.py)..." -ForegroundColor Cyan
        & $pythonCmd.Source "run_studio.py"
        exit 0
    }
}

$localPython = "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe"
if (Test-Path $localPython) {
    if (Test-Path "desktop_app.py") {
        & $localPython "desktop_app.py"
        exit 0
    }
}

Write-Host "[ERROR] Python not found! Please install Python 3.10-3.14." -ForegroundColor Red
Read-Host "Press Enter to exit..."
