# Start the Flask WhatsApp bridge (app.py) in a new window
# Usage: ./scripts/start_flask.ps1 [-RasaUrl http://localhost:5005] [-Port 8000]

param(
  [string]$RasaUrl = "http://localhost:5005",
  [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$projRoot = (Resolve-Path (Join-Path $PSScriptRoot ".."))
$python = Join-Path $projRoot ".venv310\Scripts\python.exe"
if (-not (Test-Path $python)) {
  Write-Error "Python executable not found at $python. Ensure .venv310 is created."
}

# Pass environment variables for app.py
$env:RASA_URL = $RasaUrl
$env:PORT = $Port

Start-Process -FilePath $python -ArgumentList "app.py" -WorkingDirectory $projRoot -WindowStyle Normal

Write-Host "Flask WhatsApp bridge started on port $Port (RASA_URL=$RasaUrl)."