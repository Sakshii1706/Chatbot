import os
import re
import json
from typing import List, Dict, Any

import requests
from flask import Flask, request, Response, send_from_directory, url_for
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse

RASA_URL = os.environ.get("RASA_URL", "http://localhost:5005")
TICKETS_DIR = os.path.join(os.getcwd(), "tickets")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_SIGNATURE_CHECK = os.environ.get("TWILIO_SIGNATURE_CHECK", "0") in ("1", "true", "True")

app = Flask(__name__)

@app.get("/health")
def health():
    return {"status": "ok", "rasa_url": RASA_URL, "tickets_dir": TICKETS_DIR}, 200


@app.route("/tickets/<path:filename>")
def serve_ticket(filename: str):
    return send_from_directory(TICKETS_DIR, filename, as_attachment=False)


def _normalize_ticket_urls(text: str, base_url: str) -> str:
    # Find occurrences like tickets\\BMRC-....png or tickets/BMRC-....png and make them absolute URLs
    def repl(m):
        rel_path = m.group(1).replace("\\", "/")
        return f"{base_url.rstrip('/')}/{rel_path}"

    return re.sub(r"(tickets[\\/][A-Za-z0-9_.\-]+\.png)", repl, text)


@app.route("/webhook/twilio", methods=["POST"])
def twilio_webhook():
    # Optional: verify Twilio signature for production hardening
    if TWILIO_SIGNATURE_CHECK:
        if not TWILIO_AUTH_TOKEN:
            return Response("Twilio signature check enabled but TWILIO_AUTH_TOKEN is not set", status=500)
        validator = RequestValidator(TWILIO_AUTH_TOKEN)
        signature = request.headers.get("X-Twilio-Signature", "")
        # Build full URL Twilio used (includes scheme+host+path)
        url = request.url
        form = request.form.to_dict(flat=True)
        valid = False
        try:
            valid = validator.validate(url, form, signature)
        except Exception:
            valid = False
        if not valid:
            return Response("Invalid Twilio signature", status=403)
    sender = request.values.get("From", "user").strip()
    body = request.values.get("Body", "").strip()

    if not body:
        resp = MessagingResponse()
        resp.message("(empty message)")
        return Response(str(resp), mimetype="application/xml")

    payload = {"sender": sender, "message": body}

    try:
        r = requests.post(
            f"{RASA_URL}/webhooks/rest/webhook",
            json=payload,
            timeout=15,
        )
        r.raise_for_status()
        rasa_messages: List[Dict[str, Any]] = r.json() or []
    except Exception as e:
        resp = MessagingResponse()
        resp.message(f"Backend error: {e}")
        return Response(str(resp), mimetype="application/xml")

    resp = MessagingResponse()
    base_url = request.host_url.rstrip("/")

    # Relay Rasa messages to WhatsApp
    for m in rasa_messages:
        text = m.get("text")
        image = m.get("image")
        custom = m.get("custom") or {}

        # If our action included a local tickets path in text, rewrite to absolute URL
        if text:
            text = _normalize_ticket_urls(text, base_url)
            msg = resp.message(text)
            # If Rasa also sent an image URL, attach it
            if image:
                msg.media(image)
            else:
                # Heuristic: if a tickets URL exists in text, attach as media too
                m_match = re.search(r"(tickets[\\/][A-Za-z0-9_.\-]+\.png)", text)
                if m_match:
                    rel = m_match.group(1).replace("\\", "/")
                    msg.media(f"{base_url}/{rel}")
        elif image:
            msg = resp.message("")
            msg.media(image)
        elif custom and isinstance(custom, dict):
            # If a custom image/url exists
            img = custom.get("image") or custom.get("media")
            if img:
                msg = resp.message(custom.get("text", ""))
                msg.media(img)
            else:
                resp.message(json.dumps(custom))
        else:
            # Fallback if unknown payload
            resp.message("(no content)")

    return Response(str(resp), mimetype="application/xml")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
