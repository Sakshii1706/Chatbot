# Check a booking by reference via REST webhook
# Usage: ./scripts/check_booking.ps1 -Ref BMRC-123456-7890 [-Sender demo]

param(
  [Parameter(Mandatory=$true)]
  [string]$Ref,
  [string]$Sender = "demo"
)

$body = @{ sender = $Sender; message = "Check my booking $Ref" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:5005/webhooks/rest/webhook -ContentType 'application/json' -Body $body | ConvertTo-Json -Depth 6