@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
title 🎬 SN TOOL - STUDIO PRO (AI Drama Dubbing Studio)
color 0e
cls

echo ========================================================================
echo  🎬 Launching SN TOOL - STUDIO PRO (Native Desktop Application)...
echo  🎙️ Official Voiceover Models: Piseth (Male Solo) ^& Sreymom (Female Solo)
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

if exist "dist\SN_TOOL\SN_TOOL.exe" (
    echo [INFO] Python is not installed. Launching via Standalone EXE...
    start "" "dist\SN_TOOL\SN_TOOL.exe"
    goto :END
)

if exist "SN_TOOL.exe" (
    start "" "SN_TOOL.exe"
    goto :END
)

echo [ERROR] Python not found! Please install Python 3.10-3.14.
pause

:END
echo.
echo ========================================================================
echo  [INFO] SN TOOL application has closed.
echo  👉 Press any key to exit this window...
echo ========================================================================
pause >nul
