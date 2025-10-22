# Set Twilio Messaging Service inbound webhook URL (for WhatsApp senders using a Messaging Service)
# Requires environment variables TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN.
# Usage:
#   ./scripts/set_twilio_webhook.ps1 -ServiceSid MGXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX -WebhookUrl https://<host>/webhook/twilio

param(
  [Parameter(Mandatory=$true)]
  [string]$ServiceSid,
  [Parameter(Mandatory=$true)]
  [string]$WebhookUrl
)

$ErrorActionPreference = "Stop"

if (-not $env:TWILIO_ACCOUNT_SID -or -not $env:TWILIO_AUTH_TOKEN) {
  throw "Please set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN environment variables."
}

# Twilio Messaging Service update endpoint
$uri = "https://messaging.twilio.com/v1/Services/$ServiceSid"

# InboundRequestUrl controls where inbound messages are POSTed
$body = @{ InboundRequestUrl = $WebhookUrl }

try {
  $resp = Invoke-RestMethod -Method Post -Uri $uri -Body $body -Authentication Basic -Credential (New-Object System.Management.Automation.PSCredential($env:TWILIO_ACCOUNT_SID,(ConvertTo-SecureString $env:TWILIO_AUTH_TOKEN -AsPlainText -Force)))
  $resp | ConvertTo-Json -Depth 6
  Write-Host "Updated Messaging Service $ServiceSid InboundRequestUrl -> $WebhookUrl" -ForegroundColor Green
} catch {
  Write-Error $_
}