@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
title 👑 SN STUDIO - ADMIN KEY GENERATOR
color 0a
cls

echo ========================================================================
echo  👑 កំពុងដំណើរការ SN STUDIO - ADMIN KEY GENERATOR (PORT 8888)...
echo  🔐 ប្រព័ន្ធបង្កើត និងគ្រប់គ្រង VIP License Key ជូនអតិថិជន
echo ========================================================================
echo.

:: 1. Normal launch: Try python in PATH
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    if exist "ADMIN_KEY_GENERATOR.py" (
        python ADMIN_KEY_GENERATOR.py
        if %ERRORLEVEL% NEQ 0 pause
        goto :END
    )
    if exist "admin_dashboard.py" (
        python admin_dashboard.py
        if %ERRORLEVEL% NEQ 0 pause
        goto :END
    )
)

:: 2. Try Python 3.14 via py launcher
py -3.14 --version >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    if exist "ADMIN_KEY_GENERATOR.py" (
        py -3.14 ADMIN_KEY_GENERATOR.py
        if %ERRORLEVEL% NEQ 0 pause
        goto :END
    )
    if exist "admin_dashboard.py" (
        py -3.14 admin_dashboard.py
        if %ERRORLEVEL% NEQ 0 pause
        goto :END
    )
)

:: 3. Try Python 3.12 via py launcher
py -3.12 --version >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    if exist "ADMIN_KEY_GENERATOR.py" (
        py -3.12 ADMIN_KEY_GENERATOR.py
        if %ERRORLEVEL% NEQ 0 pause
        goto :END
    )
    if exist "admin_dashboard.py" (
        py -3.12 admin_dashboard.py
        if %ERRORLEVEL% NEQ 0 pause
        goto :END
    )
)

:: 4. Try generic py launcher
py --version >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    if exist "ADMIN_KEY_GENERATOR.py" (
        py ADMIN_KEY_GENERATOR.py
        if %ERRORLEVEL% NEQ 0 pause
        goto :END
    )
    if exist "admin_dashboard.py" (
        py admin_dashboard.py
        if %ERRORLEVEL% NEQ 0 pause
        goto :END
    )
)

:: 5. Try known local Python 3.14 paths (Current PC - User M)
if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" (
    if exist "ADMIN_KEY_GENERATOR.py" (
        "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" ADMIN_KEY_GENERATOR.py
        if %ERRORLEVEL% NEQ 0 pause
        goto :END
    )
    if exist "admin_dashboard.py" (
        "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" admin_dashboard.py
        if %ERRORLEVEL% NEQ 0 pause
        goto :END
    )
)

:: 6. Try Programs Python 3.12 (User Profile / General)
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    if exist "ADMIN_KEY_GENERATOR.py" (
        "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" ADMIN_KEY_GENERATOR.py
        if %ERRORLEVEL% NEQ 0 pause
        goto :END
    )
    if exist "admin_dashboard.py" (
        "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" admin_dashboard.py
        if %ERRORLEVEL% NEQ 0 pause
        goto :END
    )
)

:: 7. Try Programs Python 3.14
if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" (
    if exist "ADMIN_KEY_GENERATOR.py" (
        "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" ADMIN_KEY_GENERATOR.py
        if %ERRORLEVEL% NEQ 0 pause
        goto :END
    )
)

:: 8. Try TUF Laptop specific path
if exist "C:\Users\TUF\AppData\Local\Programs\Python\Python312\python.exe" (
    if exist "ADMIN_KEY_GENERATOR.py" (
        "C:\Users\TUF\AppData\Local\Programs\Python\Python312\python.exe" ADMIN_KEY_GENERATOR.py
        if %ERRORLEVEL% NEQ 0 pause
        goto :END
    )
)

:: 9. Try UV CPython path
if exist "%USERPROFILE%\AppData\Roaming\uv\python\cpython-3.14.6-windows-x86_64-none\python.exe" (
    if exist "ADMIN_KEY_GENERATOR.py" (
        "%USERPROFILE%\AppData\Roaming\uv\python\cpython-3.14.6-windows-x86_64-none\python.exe" ADMIN_KEY_GENERATOR.py
        if %ERRORLEVEL% NEQ 0 pause
        goto :END
    )
)

:: 10. Fallback: Run Standalone Executable (.EXE)
if exist "dist\ADMIN_KEY_GENERATOR\ADMIN_KEY_GENERATOR.exe" (
    echo [INFO] Python មិនទាន់បានដំឡើង ដូច្នេះកំពុងបើកដំណើរការតាមរយៈ Standalone EXE...
    start "" "dist\ADMIN_KEY_GENERATOR\ADMIN_KEY_GENERATOR.exe"
    goto :END
)

if exist "ADMIN_KEY_GENERATOR.exe" (
    echo [INFO] Python មិនទាន់បានដំឡើង ដូច្នេះកំពុងបើកដំណើរការតាមរយៈ Standalone EXE...
    start "" "ADMIN_KEY_GENERATOR.exe"
    goto :END
)

echo [ERROR] Python not found and ADMIN_KEY_GENERATOR.exe not found!
echo Please make sure Python 3.10-3.14 is installed.
pause

:END
