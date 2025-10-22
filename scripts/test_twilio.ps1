# Simulate a Twilio WhatsApp webhook to the Flask bridge
# Usage: ./scripts/test_twilio.ps1 [-From "+15555555555"] [-Body "hi"] [-Url "http://localhost:8000/webhook/twilio"]

param(
  [string]$From = "+15555555555",
  [string]$Body = "hi",
  [string]$Url = "http://localhost:8000/webhook/twilio"
)

try {
  $resp = Invoke-RestMethod -Method Post -Uri $Url -ContentType "application/x-www-form-urlencoded" -Body @{ From = $From; Body = $Body }
  $resp  # TwiML XML
} catch {
  Write-Error $_
}