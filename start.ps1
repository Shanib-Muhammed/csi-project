param(
    [string]$Port = "COM6",
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv")) {
    if ($SkipInstall) {
        throw "Virtual environment not found. Run without -SkipInstall first."
    }
    py -3 -m venv .venv
}

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Python 3 virtual environment is missing. Install Python 3 and run this script again."
}

if (-not $SkipInstall) {
    & $python -m pip install --upgrade pip
    & $python -m pip install -r requirements.txt
}

$configPath = Join-Path $PSScriptRoot "config.json"
$config = Get-Content $configPath -Raw | ConvertFrom-Json
if ($Port -eq "NONE") {
    $config.serial_port = $null
    Write-Host "Serial disabled. The dashboard will show hardware disconnected; no sensor data is simulated."
} else {
    $config.serial_port = $Port
    Write-Host "Using receiver serial port: $Port"
}
$config | ConvertTo-Json -Depth 5 | Set-Content $configPath -Encoding UTF8

Write-Host "Starting Wi-Fi Sense Radar at http://127.0.0.1:8000"
& $python -m backend.main
