param(
  [Parameter(Mandatory=$true)]
  [string]$Text
)

$body = @{ text = $Text } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:5005/model/parse -ContentType 'application/json' -Body $body | ConvertTo-Json -Depth 6
