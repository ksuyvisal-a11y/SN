@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
title 🎬 SN TOOL - STUDIO PRO
color 0e
cls

echo ========================================================================
echo  🎬 Launching SN TOOL - STUDIO PRO (AI Drama Dubbing Studio)...
echo ========================================================================
echo.

if exist "%~dp0SN_TOOL.exe" (
    start "" "%~dp0SN_TOOL.exe"
    exit
)

if exist "%~dp0..\..\SN_TOOL.bat" (
    echo [INFO] Launching via SN_TOOL.bat...
    call "%~dp0..\..\SN_TOOL.bat"
    goto :END
)

if exist "%~dp0..\..\desktop_app.py" (
    where python >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        python "%~dp0..\..\desktop_app.py"
        goto :END
    )
    py -3.14 "%~dp0..\..\desktop_app.py"
    goto :END
)

echo.
echo ========================================================================
echo  ⚠️ SN_TOOL.exe not found!
echo  🛡️  Cause: Windows Defender / Antivirus may have quarantined the file.
echo  👉 Resolution:
echo     1. Open Windows Security -> Virus & threat protection -> Protection history
echo     2. Locate recent blocked item -> Actions -> Allow on device
echo     3. Or launch using "SN_TOOL.bat" in workspace root directly!
echo ========================================================================
pause

:END
