# Drives a short end-to-end booking conversation over REST
# Usage: ./scripts/demo_conversation.ps1 [-Sender demo] [-Source Majestic] [-Destination Indiranagar] [-When "today 6 pm"] [-Seats 2]

param(
  [string]$Sender = "demo",
  [string]$Source = "Majestic",
  [string]$Destination = "Indiranagar",
  [string]$When = "today 6 pm",
  [int]$Seats = 2
)

function Send-Msg {
  param([string]$Text)
  $body = @{ sender = $Sender; message = $Text } | ConvertTo-Json
  $resp = Invoke-RestMethod -Method Post -Uri http://localhost:5005/webhooks/rest/webhook -ContentType 'application/json' -Body $body
  $resp | ConvertTo-Json -Depth 6
}

Write-Host "Starting conversation for sender '$Sender'..."
Send-Msg "hi"
Start-Sleep -Milliseconds 400
Send-Msg "I want to book a metro ticket"
Start-Sleep -Milliseconds 400
Send-Msg $Source
Start-Sleep -Milliseconds 400
Send-Msg $Destination
Start-Sleep -Milliseconds 400
Send-Msg $When
Start-Sleep -Milliseconds 400
Send-Msg "$Seats"
Write-Host "Conversation complete. If payment succeeded, a QR image should be saved under tickets/."