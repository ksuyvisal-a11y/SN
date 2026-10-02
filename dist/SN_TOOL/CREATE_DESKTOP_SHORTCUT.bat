
@echo off
chcp 65001 > nul
cd /d "%~dp0"
title 🎬 SN TOOL - Create Desktop Shortcut
color 0a
cls

echo ========================================================================
echo  🎬 កំពុងបង្កើត Icon កម្មវិធី SN TOOL - STUDIO PRO លើ Desktop...
echo ========================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ws = New-Object -ComObject WScript.Shell; " ^
    "$desk = [System.Environment]::GetFolderPath('Desktop'); " ^
    "$sc = $ws.CreateShortcut(\"$desk\SN TOOL - STUDIO PRO.lnk\"); " ^
    "$sc.TargetPath = \"%~dp0SN_TOOL.exe\"; " ^
    "$sc.WorkingDirectory = \"%~dp0\"; " ^
    "$sc.IconLocation = \"%~dp0icon.ico,0\"; " ^
    "$sc.Description = 'SN TOOL - Studio Pro (Khmer AI Drama Studio)'; " ^
    "$sc.Save(); " ^
    "Write-Host '[OK] បានបង្កើត Shortcut លើ Desktop រួចរាល់ដោយជោគជ័យ!' -ForegroundColor Green"

echo.
echo ========================================================================
echo  🎉 រួចរាល់! ឥឡូវបងអាចចុចបើកកម្មវិធីបានពីលើ Desktop ភ្លាមៗ!
echo ========================================================================
echo.
pause
