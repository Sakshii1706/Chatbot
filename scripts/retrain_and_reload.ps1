# Retrain a model and hot-reload it into the running Rasa server
# Usage: ./scripts/retrain_and_reload.ps1 [-FixedName latest]

param(
  [string]$FixedName = "latest"
)

$ErrorActionPreference = "Stop"
$projRoot = (Resolve-Path (Join-Path $PSScriptRoot ".."))
$python = Join-Path $projRoot ".venv310\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Python not found at $python" }

Write-Host "Training model... (fixed name: $FixedName)"
& $python -m rasa train --fixed-model-name $FixedName --augmentation 0

$modelPath = Join-Path $projRoot ("models\{0}.tar.gz" -f $FixedName)
if (-not (Test-Path $modelPath)) { throw "Model not found: $modelPath" }

Write-Host "Reloading model into running server: $modelPath"
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $projRoot "scripts\load_model.ps1") -ModelPath $modelPath

Write-Host "Done. Check server status with ./scripts/status.ps1"