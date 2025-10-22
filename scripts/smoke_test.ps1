param(
  [Parameter(Mandatory=$true)]
  [string]$Message
)

$body = @{ sender = "test"; message = $Message } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:5005/webhooks/rest/webhook -ContentType 'application/json' -Body $body | ConvertTo-Json -Depth 6
