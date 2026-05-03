param(
    [string]$SharePath = "",
    [switch]$AskShareFile,
    [switch]$NoExtension
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$ProfilePath = Join-Path $ProjectRoot "config\default_profile.json"

function Resolve-Python {
    if (Test-Path $VenvPython) {
        return $VenvPython
    }

    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        & py -3.11 -m venv (Join-Path $ProjectRoot ".venv")
    } else {
        $python = Get-Command python -ErrorAction SilentlyContinue
        if (-not $python) {
            throw "Python 3.10 or 3.11 was not found. Install Python, then run this launcher again."
        }
        & python -m venv (Join-Path $ProjectRoot ".venv")
    }

    if (-not (Test-Path $VenvPython)) {
        throw "Could not create the project virtual environment."
    }
    return $VenvPython
}

function Ensure-ProjectInstalled($PythonExe) {
    Push-Location $ProjectRoot
    try {
        & $PythonExe -m pip install --upgrade pip
        & $PythonExe -m pip install -r requirements.txt
        & $PythonExe -m pip install -e .
    } finally {
        Pop-Location
    }
}

if ($AskShareFile) {
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.Title = "Choose a file to share through gestures"
    $dialog.Multiselect = $false
    if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        $SharePath = $dialog.FileName
    }
}

$PythonExe = Resolve-Python
Ensure-ProjectInstalled $PythonExe

$argsList = @(
    "-m", "gesture_control",
    "--camera", "-1",
    "--enable-actions",
    "--profile", $ProfilePath,
    "--show-debug",
    "--ui-scale", "0.5"
)

if (-not $NoExtension) {
    $argsList += "--enable-extension"
}

if ($SharePath -ne "") {
    $argsList += @("--share-path", $SharePath)
}

Write-Host ""
Write-Host "Starting Hand Gesture Control..."
Write-Host "Close the camera window or press q to stop."
Write-Host ""

Push-Location $ProjectRoot
try {
    & $PythonExe @argsList
} finally {
    Pop-Location
}
