@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
title 🎬 SN TOOL - STUDIO PRO (Khmer AI Drama Studio)
color 0e
cls

echo ========================================================================
echo  🎬 កំពុងបើកដំណើរ SN TOOL - STUDIO PRO (Native Desktop Application)...
echo  🎙️ សំឡេងខ្មែរផ្លូវការ: ពិសិដ្ឋ (Piseth - តួប្រុស) ^& ស្រីម (Sreymom - តួស្រី)
echo ========================================================================
echo.

:: 1. Developer / Studio Mode: Run directly via Python (No .exe, No License Gate prompt)

:: 2. Normal launch: Start Native Desktop App via Python
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    if exist "desktop_app.py" (
        python desktop_app.py
        if %ERRORLEVEL% NEQ 0 pause
        goto :END
    )
    python run_studio.py
    if %ERRORLEVEL% NEQ 0 pause
    goto :END
)

py -3.14 --version >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -3.14 desktop_app.py
    if %ERRORLEVEL% NEQ 0 pause
    goto :END
)

if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" (
    "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" desktop_app.py
    if %ERRORLEVEL% NEQ 0 pause
    goto :END
)

echo [ERROR] Python not found! Please install Python 3.10-3.14.
pause

:END

