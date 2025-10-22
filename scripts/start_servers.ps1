$ErrorActionPreference = "Stop"
# Resolve paths relative to this script's folder
$projRoot = (Resolve-Path (Join-Path $PSScriptRoot ".."))
$python = Join-Path $projRoot ".venv310\Scripts\python.exe"
# Pick the newest model automatically, fallback to models\latest.tar.gz
$modelsDir = Join-Path $projRoot "models"
if (Test-Path $modelsDir) {
  $latest = Get-ChildItem -Path $modelsDir -Filter "*.tar.gz" -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
}
$modelPath = if ($latest) { $latest.FullName } else { Join-Path $modelsDir "latest.tar.gz" }
$logsDir = Join-Path $projRoot "logs"
if (-not (Test-Path $logsDir)) {
  New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
}

if (-not (Test-Path $python)) {
  Write-Error "Python executable not found at $python. Ensure .venv310 is created."
}

# Start Action Server in a new window
Start-Process -FilePath $python -ArgumentList "-m rasa run actions --port 5055" -WorkingDirectory $projRoot -WindowStyle Normal
Start-Sleep -Seconds 2

# Start Rasa Server with API and pinned model in a new window
$logFile = Join-Path $logsDir "server.log"
Start-Process -FilePath $python -ArgumentList ("-m rasa run --enable-api --cors `"*`" --port 5005 --model `"{0}`" --log-file `"{1}`"" -f $modelPath, $logFile) -WorkingDirectory $projRoot -WindowStyle Normal

Write-Host "Started action server (5055) and Rasa server (5005) in separate windows. Give it ~20-40s on first start."