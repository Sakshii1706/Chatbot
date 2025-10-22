# Bangalore Metro Ticketing Chatbot

End-to-end Rasa 3.x chatbot for booking Bangalore Metro tickets with bilingual prompts, slot-filling forms, QR e-tickets, and booking lookup. See scripts in `scripts/` and configuration in `domain.yml`, `data/`, and `endpoints.yml`.

## Quick start (Windows PowerShell)

Prerequisites:
- Python 3.10
- Repo cloned locally
- Virtual env with Rasa installed (this project uses `.venv310`)

Install dependencies:

	. .\.venv310\Scripts\Activate.ps1
	pip install -r requirements.txt

Start servers (recommended script):

	./scripts/start_servers.ps1

Check status:

	./scripts/status.ps1

Smoke test via REST (script):

	# One-shot conversation driver (recommended)
	./scripts/demo_conversation.ps1

	# Or send a single message
	./scripts/smoke_test.ps1 -Message "hi"

Check booking by reference:

	./scripts/check_booking.ps1 -Ref BMRC-123456-7890

Manual REST calls (examples):

	# Greet
	Invoke-RestMethod -Method Post -Uri "http://localhost:5005/webhooks/rest/webhook" -ContentType 'application/json' -Body (@{ sender="demo"; message="hi" } | ConvertTo-Json)

	# Start booking
	Invoke-RestMethod -Method Post -Uri "http://localhost:5005/webhooks/rest/webhook" -ContentType 'application/json' -Body (@{ sender="demo"; message="I want to book a metro ticket" } | ConvertTo-Json)

	# Provide source
	Invoke-RestMethod -Method Post -Uri "http://localhost:5005/webhooks/rest/webhook" -ContentType 'application/json' -Body (@{ sender="demo"; message="Majestic" } | ConvertTo-Json)

	# Provide destination
	Invoke-RestMethod -Method Post -Uri "http://localhost:5005/webhooks/rest/webhook" -ContentType 'application/json' -Body (@{ sender="demo"; message="Indiranagar" } | ConvertTo-Json)

	# Provide travel time
	Invoke-RestMethod -Method Post -Uri "http://localhost:5005/webhooks/rest/webhook" -ContentType 'application/json' -Body (@{ sender="demo"; message="today 6 pm" } | ConvertTo-Json)

	# Provide seats (1-6)
	Invoke-RestMethod -Method Post -Uri "http://localhost:5005/webhooks/rest/webhook" -ContentType 'application/json' -Body (@{ sender="demo"; message="2" } | ConvertTo-Json)

Expected: The bot checks availability, simulates payment, and returns a booking reference with a QR PNG saved under `tickets/`.

Stop servers:

	./scripts/stop_servers.ps1

All-in-one start (servers + bridge + ngrok):

	./scripts/start_all.ps1 -RasaUrl http://localhost:5005 -Port 8000

## Model management

Hot-reload the running model:

	./scripts/load_model.ps1 -ModelPath models\latest.tar.gz

Retrain and hot-reload in one step:

	./scripts/retrain_and_reload.ps1

Retrain (quick):

	. .\.venv310\Scripts\Activate.ps1
	rasa train --fixed-model-name latest --augmentation 0

Dev loop (validate → train → reload → status → demo):

	./scripts/dev_loop.ps1

## WhatsApp (Twilio) bridge

`app.py` provides a Flask webhook to bridge WhatsApp → Rasa REST and serves QR images.

Start the bridge:

	./scripts/start_flask.ps1 -RasaUrl http://localhost:5005 -Port 8000

Expose publicly and print webhook URL:

	./scripts/ngrok.ps1 -Port 8000

Test locally (simulate Twilio):

	./scripts/test_twilio.ps1 -From "+15555555555" -Body "hi" -Url "http://localhost:8000/webhook/twilio"

Configure Twilio WhatsApp sandbox to point to:

	http://<public-host-or-ngrok>:8000/webhook/twilio

Health check:

	Invoke-RestMethod -Method Get -Uri http://localhost:8000/health | ConvertTo-Json -Depth 5

Notes:
- The bridge rewrites any local ticket paths like `tickets\BMRC-....png` into absolute URLs, so WhatsApp can display the QR image.
- Override RASA_URL/PORT via script params or environment variables.
 - Optional production hardening: enable signature validation by setting env vars before starting the bridge:

	$env:TWILIO_SIGNATURE_CHECK = "1" ; $env:TWILIO_AUTH_TOKEN = "<your_auth_token>"
	./scripts/start_flask.ps1 -RasaUrl http://localhost:5005 -Port 8000

 - To set the webhook URL on a Twilio Messaging Service via API (instead of Console):

	$env:TWILIO_ACCOUNT_SID = "AC..."
	$env:TWILIO_AUTH_TOKEN  = "..."
	./scripts/set_twilio_webhook.ps1 -ServiceSid MGXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX -WebhookUrl https://<public-host>/webhook/twilio

## Troubleshooting

- Slow startup: First run warms up TensorFlow on Windows; subsequent starts are faster.
- Port in use: If 5005/5055 are occupied, stop previous instances or change ports (e.g., `--port 5006`).
- PowerShell quoting: Build JSON with `@{...} | ConvertTo-Json` to avoid escaping issues.
- Validation: After changing YAML, run `python -m rasa data validate`.
- Or use the helper script: `./scripts/validate.ps1`.
- QR path: Tickets are saved under `tickets/` as `BMRC-<timestamp>-<suffix>.png`.

## Structure (high level)

- `domain.yml` — intents, slots, forms, responses, actions list
- `data/` — NLU, stories, rules
- `actions/` — validators and actions (availability, payment, QR, DB)
- `app.py` — Flask bridge for WhatsApp
- `/health` on Flask returns a simple JSON status.
- `endpoints.yml` — action server URL
- `scripts/` — helper PowerShell scripts
- `tickets/` — generated QR e-tickets
- `models/` — trained Rasa models
- `logs/` — server logs

## Notes

- Seats slot mapping is restricted to only accept input when the form explicitly asks for it, preventing digits from other messages (e.g., "6 pm") from being misinterpreted as seats.