@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
title 👑 SN TOOL - VIP License Admin Dashboard
color 0b
cls

echo ========================================================================
echo  👑 SN TOOL - VIP LICENSE ADMIN DASHBOARD (ORION LIGHT THEME)
echo  🔐 ប្រព័ន្ធគ្រប់គ្រង និងបង្កើត KEY ជូនអតិថិជន
echo ========================================================================
echo.
echo [INFO] កំពុងចាប់ផ្តើម Server និងបើក Dashboard ក្នុង Browser...
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
