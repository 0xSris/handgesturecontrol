$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Launcher = Join-Path $ProjectRoot "Start Gesture Control.bat"

if (-not (Test-Path $Launcher)) {
    throw "Launcher not found: $Launcher"
}

$ProtocolRoot = "HKCU:\Software\Classes\hgc"
$CommandKey = Join-Path $ProtocolRoot "shell\open\command"

New-Item -Path $CommandKey -Force | Out-Null
Set-Item -Path $ProtocolRoot -Value "URL:Hand Gesture Control"
New-ItemProperty -Path $ProtocolRoot -Name "URL Protocol" -Value "" -PropertyType String -Force | Out-Null

$Command = "cmd.exe /c start """" ""$Launcher"""
Set-Item -Path $CommandKey -Value $Command

Write-Host "Done. The extension can now start the desktop app with hgc://start."
