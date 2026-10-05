@echo off
chcp 65001 > nul
cd /d "%~dp0"
title 👑 SN STUDIO - ADMIN KEY GENERATOR
color 0a
cls

echo ========================================================================
echo  👑 កំពុងដំណើរការ SN STUDIO - ADMIN KEY GENERATOR (PORT 8888)...
echo ========================================================================
echo.

if exist "C:\Users\TUF\AppData\Local\Programs\Python\Python312\python.exe" (
    "C:\Users\TUF\AppData\Local\Programs\Python\Python312\python.exe" ADMIN_KEY_GENERATOR.py
) else (
    python ADMIN_KEY_GENERATOR.py
)

pause
