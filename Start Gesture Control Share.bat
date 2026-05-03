@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_gesture_control.ps1" -AskShareFile
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_gesture_control.ps1" -SharePath "%~1"
)
pause
