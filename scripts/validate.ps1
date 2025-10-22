<#
Run Rasa data validation and optionally filter noisy warnings about form utterances
Usage:
	./scripts/validate.ps1              # quiet (filters form-utterance warnings)
	./scripts/validate.ps1 -ShowAll     # show full validator output
#>

param(
	[switch]$ShowAll
)

$projRoot = (Resolve-Path (Join-Path $PSScriptRoot ".."))
$python = Join-Path $projRoot ".venv310\Scripts\python.exe"

$output = & $python -m rasa data validate 2>&1

if ($ShowAll) {
	$output
} else {
	$pattern = "The utterance 'utter_(ask_(source|destination|date_time|seats|booking_ref)|submit)' is not used in any story or rule\."
	$output | Where-Object { $_ -notmatch $pattern }
}