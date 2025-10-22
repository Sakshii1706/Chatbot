# Poll /status until it responds or timeout (~60s)
for ($i=0; $i -lt 12; $i++) {
  try {
    $r = Invoke-RestMethod -Method Get -Uri http://localhost:5005/status
    $r | ConvertTo-Json -Depth 6
    break
  } catch {
    Start-Sleep -Seconds 5
  }
}
