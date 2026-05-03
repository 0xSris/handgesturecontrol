@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -Command "Unregister-ScheduledTask -TaskName 'Hand Gesture Control' -Confirm:$false -ErrorAction SilentlyContinue; Write-Host 'Background startup task removed.'"
pause
