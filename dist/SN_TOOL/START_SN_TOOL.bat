@echo off
chcp 65001 > nul
cd /d "%~dp0"
title 🎬 SN TOOL - STUDIO PRO
color 0b
cls

echo ========================================================================
echo  🎬 កំពុងដំណើរការ SN TOOL - STUDIO PRO (Khmer AI Drama Voice Studio)...
echo ========================================================================
echo.

start "" "%~dp0SN_TOOL.exe"
exit
