@echo off
chcp 65001 > nul
cd /d "%~dp0"
title 🎬 SN STUDIO - Khmer AI Drama Voice Studio (Piseth & Sreymom)
color 0e
cls

echo ========================================================================
echo  🎬 កំពុងបើកដំណើរការ SN STUDIO (Khmer AI Drama Voice Studio)...
echo  🎙️ សំឡេងខ្មែរផ្លូវការ: ពិសិដ្ឋ (Piseth) & ស្រីមុំ (Sreymom)
echo  🌐 http://localhost:8000
echo ========================================================================
echo.

:: 1. If a video file is dragged and dropped onto SN_TOOL.bat, translate it directly
if not "%~1"=="" (
    echo ========================================================================
    echo  🚀 បានទទួលឯកសារវីដេអូដែលបានទម្លាក់ចូល (Drag ^& Drop 1-Click Dubbing):
    echo  📁 %~1
    echo ========================================================================
    echo.
    python translate_video.py --video "%~1"
    if %ERRORLEVEL% NEQ 0 (
        py -3.14 translate_video.py --video "%~1"
    )
    if exist "data\exports" explorer "data\exports"
    pause
    exit /b 0
)

:: 2. Normal launch: Start Web Studio immediately without any pause or prompt
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python run_studio.py
    goto :END
)

py -3.14 --version >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -3.14 run_studio.py
    goto :END
)

if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" (
    "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" run_studio.py
    goto :END
)

echo [ERROR] Python not found! Please install Python 3.10-3.14.
pause

:END
