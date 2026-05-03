$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Launcher = Join-Path $ProjectRoot "Start Gesture Control.bat"

if (-not (Test-Path $Launcher)) {
    throw "Launcher not found: $Launcher"
}

$Action = New-ScheduledTaskAction -Execute $Launcher -WorkingDirectory $ProjectRoot
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DisallowStartIfOnBatteries:$false -ExecutionTimeLimit (New-TimeSpan -Hours 8)

Register-ScheduledTask `
    -TaskName "Hand Gesture Control" `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Starts the hand gesture controller when Windows starts." `
    -Force | Out-Null

Write-Host "Done. Hand Gesture Control will start automatically when you sign in."
