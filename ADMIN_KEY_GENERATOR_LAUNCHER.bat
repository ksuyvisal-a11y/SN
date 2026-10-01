@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
title ⚡ SN TOOL - Admin License Key Generator Dashboard
color 0b
cls
echo ========================================================
echo  ⚡ SN TOOL - ADMIN LICENSE KEY GENERATOR DASHBOARD
echo  🔐 ប្រព័ន្ធបង្កើត និងគ្រប់គ្រង KEY ជូនទៅកាន់ CUSTOMER
echo ========================================================
echo.
python admin_dashboard.py
if %ERRORLEVEL% NEQ 0 (
    py admin_dashboard.py
)
pause

