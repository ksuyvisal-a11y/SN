@echo off
chcp 65001 > nul
cd /d "%~dp0"
title 🎬 SN TOOL - STUDIO PRO
cls
echo ========================================================================
echo  🎬 កំពុងបើកដំណើរ SN TOOL - STUDIO PRO...
echo ========================================================================
start "" "%~dp0SN_TOOL.exe"
exit
