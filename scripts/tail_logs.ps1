param(
  [string]$Path = (Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..")) "logs\server.log"),
  [int]$Seconds = 60
)
Write-Host "Tailing $Path for $Seconds seconds..."
for ($i=0; $i -lt $Seconds; $i++) {
  if (Test-Path $Path) {
    Get-Content $Path -Tail 10
  } else {
    Write-Host "Log file not found yet..."
  }
  Start-Sleep -Seconds 1
}
