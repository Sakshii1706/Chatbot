<#
Start ngrok to expose the Flask bridge port and print the public URL (Twilio-ready)
Requires ngrok in PATH.
Usage: ./scripts/ngrok.ps1 [-Port 8000]
#>

param(
  [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

try {
  # Start ngrok in a new window so it stays alive
  Start-Process -FilePath "ngrok" -ArgumentList "http $Port" -WindowStyle Normal
  Write-Host "ngrok starting for port $Port..."
  # Poll local ngrok API for the tunnel public URL
  $publicUrl = $null
  for ($i=0; $i -lt 20; $i++) {
    try {
      $tunnels = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:4040/api/tunnels" -ErrorAction Stop
      $https = $tunnels.tunnels | Where-Object { $_.public_url -like "https*" } | Select-Object -First 1
      $http = $tunnels.tunnels | Where-Object { $_.public_url -like "http://*" } | Select-Object -First 1
      if ($https) { $publicUrl = $https.public_url; break }
      elseif ($http) { $publicUrl = $http.public_url; break }
    } catch {
      Start-Sleep -Seconds 1
    }
  }

  if ($publicUrl) {
    Write-Host "Public URL: $publicUrl" -ForegroundColor Green
    Write-Host "Twilio Webhook (paste this): $publicUrl/webhook/twilio" -ForegroundColor Green
  } else {
    Write-Warning "Couldn't fetch public URL from ngrok yet. Once it appears, set your Twilio webhook to: http(s)://<forwarding-host>/webhook/twilio"
  }
} catch {
  Write-Error "Failed to start or query ngrok. Ensure ngrok is installed and in PATH. $_"
}