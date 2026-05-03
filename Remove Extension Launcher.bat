@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -Command "Remove-Item -Path 'HKCU:\Software\Classes\hgc' -Recurse -Force -ErrorAction SilentlyContinue; Write-Host 'Extension launcher removed.'"
pause
