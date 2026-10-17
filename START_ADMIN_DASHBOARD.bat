@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
title 👑 SN TOOL - License Admin Control Center (Port 8888)
color 0b
cls

echo ========================================================================
echo  👑 SN TOOL - LICENSE ADMIN CONTROL CENTER (ORION LIGHT THEME)
echo  🛡️  Port: 8888 (Dedicated Admin Control Center - Isolated from Port 8000)
echo  🔐 License Key Management & Generation System
echo ========================================================================
echo.
echo [INFO] Starting Admin Server (Port 8888) and opening Browser...
echo.

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python admin_dashboard.py
    if %ERRORLEVEL% NEQ 0 pause
    goto :END
)

py -3.14 --version >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -3.14 admin_dashboard.py
    if %ERRORLEVEL% NEQ 0 pause
    goto :END
)

if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" (
    "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" admin_dashboard.py
    if %ERRORLEVEL% NEQ 0 pause
    goto :END
)

if exist "%USERPROFILE%\AppData\Roaming\uv\python\cpython-3.14.6-windows-x86_64-none\python.exe" (
    "%USERPROFILE%\AppData\Roaming\uv\python\cpython-3.14.6-windows-x86_64-none\python.exe" admin_dashboard.py
    if %ERRORLEVEL% NEQ 0 pause
    goto :END
)

echo [ERROR] Python not found! Please make sure Python is installed.
pause

:END
echo.
echo ========================================================================
echo  [INFO] ADMIN DASHBOARD process finished or closed.
echo  👉 Press Enter or any key to exit this window...
echo ========================================================================
pause >nul
