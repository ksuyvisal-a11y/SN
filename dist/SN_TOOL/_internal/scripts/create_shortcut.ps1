[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host " 📌 កំពុងបង្កើតផ្លូវកាត់លើ Desktop សម្រាប់ SN TOOL (Desktop Shortcut)..." -ForegroundColor Yellow
Write-Host "========================================================================" -ForegroundColor Cyan

$ws = New-Object -ComObject WScript.Shell
$d = (Get-Location).Path
$desktops = @(
    [Environment]::GetFolderPath('Desktop'),
    [System.IO.Path]::Combine($env:USERPROFILE, 'Desktop')
)

foreach ($dt in $desktops) {
    if ($dt -and (Test-Path $dt)) {
        $s = [System.IO.Path]::Combine($dt, "SN TOOL - STUDIO PRO.lnk")
        $sc = $ws.CreateShortcut($s)
        $sc.TargetPath = [System.IO.Path]::Combine($d, "SN_TOOL.exe")
        $sc.WorkingDirectory = $d
        $sc.IconLocation = [System.IO.Path]::Combine($d, "icon.ico") + ",0"
        $sc.Description = "SN TOOL - STUDIO PRO (Khmer AI Drama Voice Studio)"
        $sc.Save()
        Write-Host "  ✔ Created shortcut at: $s" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host " [OK] បង្កើត Desktop Shortcut ជោគជ័យ!" -ForegroundColor Green
Write-Host ""
Start-Sleep -Seconds 2
