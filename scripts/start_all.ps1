# Start Rasa + Actions, prewarm NLU, start Flask bridge, and expose via ngrok
# Usage: ./scripts/start_all.ps1 [-RasaUrl http://localhost:5005] [-Port 8000]

param(
  [string]$RasaUrl = "http://localhost:5005",
  [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$projRoot = (Resolve-Path (Join-Path $PSScriptRoot ".."))

Write-Host "[1/4] Starting Rasa + Actions..."
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $projRoot "scripts/start_servers.ps1")
Start-Sleep -Seconds 5

Write-Host "[2/4] Prewarming NLU (parse 'hi')..."
try {
  & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $projRoot "scripts/parse.ps1") -Text "hi"
} catch {
  Write-Warning "Prewarm parse failed (will continue): $($_.Exception.Message)"
}

Write-Host "[3/4] Starting Flask bridge on port $Port (RasaUrl=$RasaUrl)..."
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $projRoot "scripts/start_flask.ps1") -RasaUrl $RasaUrl -Port $Port
Start-Sleep -Seconds 2

Write-Host "[4/4] Starting ngrok and printing Twilio webhook URL..."
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $projRoot "scripts/ngrok.ps1") -Port $Port

Write-Host "\nAll services started. Paste the printed webhook URL into Twilio (…/webhook/twilio)." -ForegroundColor Green
