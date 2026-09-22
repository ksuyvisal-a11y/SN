# ==============================================================================
# 🎬 SN TOOL - STUDIO PRO (Khmer AI Drama Studio) - PowerShell Launcher
# ==============================================================================
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "🎬 SN TOOL - STUDIO PRO (Khmer AI Drama Studio)"

Write-Host "========================================================================" -ForegroundColor Yellow
Write-Host " 🎬 កំពុងបើកដំណើរ SN TOOL - STUDIO PRO (Native Desktop Application)..." -ForegroundColor Cyan
Write-Host " 🎙️ សំឡេងខ្មែរផ្លូវការ: ពិសិដ្ឋ (Piseth - តួប្រុស) & ស្រីមុំ (Sreymom - តួស្រី)" -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Yellow
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# 1. Developer / Studio Mode: Run directly via Python (No .exe, No License Gate prompt)

# 2. Check Python and launch desktop_app.py or run_studio.py
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $pythonCmd) {
    $pythonCmd = Get-Command py -ErrorAction SilentlyContinue
}

if ($pythonCmd) {
    if (Test-Path "desktop_app.py") {
        Write-Host "🖥️ កំពុងបើក Native Desktop Window (desktop_app.py)..." -ForegroundColor Cyan
        & $pythonCmd.Source "desktop_app.py"
        exit 0
    } elseif (Test-Path "run_studio.py") {
        Write-Host "🌐 កំពុងបើក Studio Web Server (run_studio.py)..." -ForegroundColor Cyan
        & $pythonCmd.Source "run_studio.py"
        exit 0
    }
}

# 3. Fallback: Local AppData Python installation
$localPython = "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe"
if (Test-Path $localPython) {
    if (Test-Path "desktop_app.py") {
        & $localPython "desktop_app.py"
        exit 0
    }
}

Write-Host "[ERROR] មិនអាចស្វែងរក Python បានទេ! សូមដំឡើង Python 3.10-3.14 រួចសាកល្បងម្តងទៀត។" -ForegroundColor Red
Read-Host "ចុច Enter ដើម្បីចាកចេញ..."
