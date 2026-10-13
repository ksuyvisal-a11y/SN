@echo off
cd /d "%~dp0"
title SN TOOL - 1-Click Update Creator
color 0b
cls

echo ========================================================================
echo  SN TOOL - 1-CLICK UPDATE AND RELEASE CREATOR
echo ========================================================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python scripts\make_release_package.py
    goto :DONE
)

py -3.14 scripts\make_release_package.py
if %ERRORLEVEL% EQU 0 goto :DONE

py scripts\make_release_package.py

:DONE
echo.
pause
