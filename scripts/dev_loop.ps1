# One-command dev loop: validate -> train -> reload -> status -> demo conversation
# Usage: ./scripts/dev_loop.ps1 [-Sender demo] [-Source Majestic] [-Destination Indiranagar] [-When "today 6 pm"] [-Seats 2]

param(
  [string]$Sender = "demo",
  [string]$Source = "Majestic",
  [string]$Destination = "Indiranagar",
  [string]$When = "today 6 pm",
  [int]$Seats = 2
)

$ErrorActionPreference = "Stop"
$projRoot = (Resolve-Path (Join-Path $PSScriptRoot ".."))

Write-Host "[1/5] Validate..."
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $projRoot "scripts/validate.ps1")

Write-Host "[2/5] Retrain and reload..."
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $projRoot "scripts/retrain_and_reload.ps1")

Write-Host "[3/5] Status..."
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $projRoot "scripts/status.ps1")

Write-Host "[4/5] Demo conversation..."
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $projRoot "scripts/demo_conversation.ps1") -Sender $Sender -Source $Source -Destination $Destination -When $When -Seats $Seats

Write-Host "[5/5] Done. Tail logs optionally with ./scripts/tail_logs.ps1"
