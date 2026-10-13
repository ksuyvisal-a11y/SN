@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
title 🎬 SN TOOL - STUDIO PRO
color 0e
cls

if not exist "%~dp0SN_TOOL.exe" (
    if exist "%~dp0SN_TOOL.exe.bak" (
        copy /y "%~dp0SN_TOOL.exe.bak" "%~dp0SN_TOOL.exe" >nul 2>&1
    )
)

if exist "%~dp0SN_TOOL.exe" (
    start "" "%~dp0SN_TOOL.exe"
    exit
)

echo.
echo ========================================================================
echo  ⚠️ SN_TOOL.exe not found!
echo  🛡️  Cause: Windows Defender / Antivirus may have quarantined the file.
echo  👉 Resolution:
echo     1. Open Windows Security -> Virus & threat protection -> Protection history
echo     2. Locate recent blocked item -> Actions -> Allow on device
echo ========================================================================
pause
