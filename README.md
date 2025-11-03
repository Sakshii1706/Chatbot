# Online Chatbot-Based Ticketing System (Rasa + WhatsApp)

This project is a Windows-friendly Rasa chatbot for Bangalore Metro ticket booking with:
- Bilingual guided form (English + Kannada) collecting source, destination, date/time, and seats
- Availability check with TTL cache, mock payment flow, QR e-ticket generation
- SQLite persistence and booking lookup by reference
- Flask bridge to Twilio WhatsApp webhook with optional signature validation
- PowerShell scripts to validate, train, start servers, run the bridge, and expose via ngrok

## Fast path to send “hi” on WhatsApp

1) Start everything and get a public URL

```powershell
./scripts/start_all.ps1 -RasaUrl http://localhost:5005 -Port 8000
```

2) In Twilio, set the inbound webhook to the printed URL
- Use {PUBLIC_URL}/webhook/twilio on your Messaging Service (or WhatsApp Sandbox page)

3) From your phone, WhatsApp “hi” to your Twilio WhatsApp number
- Sandbox: send “join <your-code>” once to the Sandbox number, then “hi”
- Business number: just send “hi”

You should receive the bilingual greeting and booking prompts.

Quick start (Windows, PowerShell)
1) Create and activate a Python 3.10 virtualenv (recommended):
	- python -m venv .venv310; .\.venv310\Scripts\Activate.ps1

2) Install dependencies:
	- python -m pip install --upgrade pip; pip install -r requirements.txt

3) Validate Rasa data and train a model:
	- .\scripts\validate.ps1
	- If needed: rasa train (or use .\scripts\retrain_and_reload.ps1)

4) Start action and Rasa servers (two terminals):
	- .\scripts\start_servers.ps1

5) Start the Flask bridge for WhatsApp (third terminal):
	- .\scripts\start_flask.ps1

6) Expose locally via ngrok (optional, required for Twilio):
	- .\scripts\ngrok.ps1
	- Copy the printed public URL and set it as your Twilio Messaging Service webhook URL for incoming messages to: {PUBLIC_URL}/webhook/twilio

7) Send a message to your WhatsApp number linked to your Twilio Sandbox/Service and say: hi
Key ports
- Rasa server: 5005
- Rasa action server: 5055
- Flask bridge: 8000

Environment variables (optional)
- RASA_URL: URL of the Rasa REST webhook (default http://localhost:5005)
- PORT: Flask port (default 8000)
- TWILIO_SIGNATURE_CHECK: true/false (default false)
- TWILIO_AUTH_TOKEN: required if signature check is enabled

Structure
- actions/          Python actions (validators, booking submit, lookup)
- data/             NLU, stories, and rules
- scripts/          PowerShell helpers (Windows)
- tickets/          Generated QR codes (served by Flask)
- app.py            Flask <-> Twilio WhatsApp bridge
- domain.yml        Intents, slots, forms, responses, actions
- config.yml        NLU pipeline and policies
- endpoints.yml     Action server configuration
- requirements.txt  Dependencies

Security notes
- Never commit secrets (Twilio tokens, etc.). Store them as environment variables.
- If you ever shared your Twilio token publicly, rotate it immediately in the Twilio Console.

Troubleshooting
- First run is slow due to TensorFlow warm-up. Be patient on Windows.
- If validation shows unused utterances, it’s benign with forms.
- If ngrok isn’t in PATH, install it from https://ngrok.com/ and ensure ngrok.exe is available.

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