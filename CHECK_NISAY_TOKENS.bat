@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
title 💎 NISAY API TOKEN CHECKER
color 0b
cls

python scripts/check_nisay_token.py
if %ERRORLEVEL% NEQ 0 (
    py -3.14 scripts/check_nisay_token.py
)

pause
