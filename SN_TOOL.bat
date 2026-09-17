@echo off
chcp 65001 > nul
cd /d "%~dp0"
title 🎬 SN STUDIO - Khmer AI Drama Voice Studio
color 0e
cls

echo ========================================================
echo  🚀 កំពុងបើកដំណើរការ SN STUDIO...
echo  🌐 http://localhost:8000
echo ========================================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python run_studio.py
) else (
    if exist "dist\SN_TOOL\SN_TOOL.exe" (
        echo រកមិនឃើញ Python ទេ! កំពុងបើកតាមរយៈ Standalone EXE...
        start "" "dist\SN_TOOL\SN_TOOL.exe"
    ) else (
        echo [ERROR] សូមដំឡើង Python ឬទាញយកជំនាន់ EXE!
    )
)

pause

