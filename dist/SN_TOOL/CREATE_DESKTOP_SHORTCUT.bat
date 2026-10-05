@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ========================================================================
echo  📌 កំពុងបង្កើតផ្លូវកាត់លើ Desktop សម្រាប់ SN TOOL (Desktop Shortcut)...
echo ========================================================================

powershell -Command ^
    "$ws = New-Object -ComObject WScript.Shell; " ^
    "$s = \"$env:USERPROFILE\Desktop\SN TOOL - STUDIO PRO.lnk\"; " ^
    "$sc = $ws.CreateShortcut($s); " ^
    "$sc.TargetPath = \"%~dp0SN_TOOL.exe\"; " ^
    "$sc.WorkingDirectory = \"%~dp0\"; " ^
    "$sc.IconLocation = \"%~dp0icon.ico,0\"; " ^
    "$sc.Description = \"SN TOOL - STUDIO PRO (Khmer AI Drama Voice Studio)\"; " ^
    "$sc.Save()"

echo.
echo [OK] បង្កើត Desktop Shortcut ជោគជ័យ!
timeout /t 3 > nul
