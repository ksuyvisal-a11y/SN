@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
title 🎬 SN TOOL - STUDIO PRO
color 0e
cls

echo ========================================================================
echo  🎬 កំពុងដំណើរការ SN TOOL - STUDIO PRO (Khmer AI Drama Studio)...
echo ========================================================================
echo.

if exist "%~dp0SN_TOOL.exe" (
    start "" "%~dp0SN_TOOL.exe"
    exit
)

if exist "%~dp0..\..\SN_TOOL.bat" (
    echo [INFO] កំពុងបើកដំណើរការតាមរយៈ SN_TOOL.bat...
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
echo  ⚠️ មិនឃើញឯកសារ SN_TOOL.exe ទេ!
echo  🛡️  មូលហេតុ៖ កម្មវិធី Windows Defender (Antivirus) បានច្រឡំលុប ឬដាក់ Quarantine
echo  👉 វិធីដោះស្រាយ៖
echo     1. សូមបើក Windows Security -> Virus & threat protection -> Protection history
echo     2. ចុចលើ Threat ចុងក្រោយ (Trojan:Win32/Bearfoos.B!ml) -> Actions -> Allow on device
echo     3. ឬបើកដំណើរការតាមឯកសារ "SN_TOOL.bat" នៅ Folder ដើមខាងក្រៅបានភ្លាមៗ!
echo ========================================================================
pause

:END
