param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot
$runtimeTmp = Join-Path $projectRoot "tmp\pyi-runtime"
New-Item -ItemType Directory -Force -Path $runtimeTmp | Out-Null

& $Python -m pip install pyinstaller
& $Python -m PyInstaller `
    --name GestureControl `
    --onedir `
    --noconfirm `
    --paths "$projectRoot\src" `
    --add-data "$projectRoot\models\hand_landmarker.task;models" `
    --add-data "$projectRoot\config\default_profile.json;config" `
    "$projectRoot\scripts\gesture_control_entry.py"

Write-Host "Built dist\GestureControl\GestureControl.exe"
