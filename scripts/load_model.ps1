param(
  [Parameter(Mandatory=$true)]
  [string]$ModelPath
)
$body = @{ model_file = $ModelPath } | ConvertTo-Json
Invoke-RestMethod -Method Put -Uri http://localhost:5005/model -ContentType 'application/json' -Body $body | ConvertTo-Json -Depth 6
