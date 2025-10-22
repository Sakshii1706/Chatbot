from __future__ import annotations
from typing import Any, Dict, List, Text
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from datetime import datetime, timedelta
from dateutil import parser as dateparser
import os
import base64
from pathlib import Path
try:
    import qrcode  # type: ignore
except Exception:
    qrcode = None
import random
import time
from .db import init_db, save_booking, get_booking, purge_older_than

# Perform lightweight DB housekeeping on action server startup (best-effort)
try:
    init_db()
    # Purge bookings older than 7 days (7 * 24 * 3600 seconds)
    purge_older_than(7 * 24 * 3600)
except Exception:
    # Non-fatal: continue even if cleanup fails
    pass

# Minimal station list for validation; replace/extend from DB/cache during runtime
VALID_STATIONS = {
    "Majestic",
    "Indiranagar",
    "MG Road",
    "Jayanagar",
    "Yelachenahalli",
    "Nagasandra",
    "Baiyappanahalli",
    "Mysuru Road",
}

# In-memory availability cache: key -> {"available": int, "updated": float}
AVAIL_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes
DEFAULT_CAPACITY = 120   # seats per route/time-slot

def _timeslot_key(source: Text, destination: Text, date_time_text: Text) -> Text:
    """Bucket the datetime to an hourly slot and compose a cache key."""
    try:
        dt = dateparser.parse(date_time_text, fuzzy=True) if isinstance(date_time_text, str) else None
    except Exception:
        dt = None
    if not dt:
        dt = datetime.now()
    slot_dt = dt.replace(minute=0, second=0, microsecond=0)
    return f"{source}->{destination}|{slot_dt.strftime('%Y-%m-%d %H:%M')}"

def _get_availability(key: Text) -> int:
    now_ts = time.time()
    rec = AVAIL_CACHE.get(key)
    if not rec or (now_ts - rec.get("updated", 0)) > CACHE_TTL_SECONDS:
        # initialize/reset capacity
        AVAIL_CACHE[key] = {"available": DEFAULT_CAPACITY, "updated": now_ts}
    return AVAIL_CACHE[key]["available"]

def _update_availability(key: Text, delta: int) -> None:
    now_ts = time.time()
    rec = AVAIL_CACHE.get(key)
    if not rec:
        rec = {"available": DEFAULT_CAPACITY, "updated": now_ts}
        AVAIL_CACHE[key] = rec
    rec["available"] = max(0, rec["available"] + delta)
    rec["updated"] = now_ts

def _ensure_dir(path: Text) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)

def _build_ticket_payload(txn_ref: Text, source: Text, destination: Text, when: Text, seats: int) -> Dict[str, Any]:
    return {
        "ref": txn_ref,
        "route": f"{source}->{destination}",
        "at": when,
        "seats": seats,
        "issuer": "BMRC-Demo",
        "ts": int(time.time()),
    }

def _make_qr_image(payload: Dict[str, Any], out_path: Text) -> Text:
    if qrcode is None:
        return ""  # qrcode not installed
    import json
    data = json.dumps(payload, separators=(",", ":"))
    img = qrcode.make(data)
    img.save(out_path)
    return out_path

class ValidateTicketForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_ticket_form"

    def validate_source(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        if value and value.strip().title() in VALID_STATIONS:
            return {"source": value.strip().title()}
        dispatcher.utter_message(text=(
            "Unknown source station. Please provide a valid station name.\n"
            "ಗೊತ್ತಿಲ್ಲದ ಪ್ರಾರಂಭ ಸ್ಟೇಷನ್. ಸರಿಯಾದ ಸ್ಟೇಷನ್ ಹೇಳಿ."
        ))
        return {"source": None}

    def validate_destination(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        if value and value.strip().title() in VALID_STATIONS:
            # avoid same source/destination
            if tracker.get_slot("source") and tracker.get_slot("source") == value.strip().title():
                dispatcher.utter_message(text=(
                    "Source and destination cannot be the same. Please choose another.\n"
                    "ಆರಂಭ ಮತ್ತು ಗಮ್ಯ ಸ್ಟೇಷನ್ ಒಂದೇ ಆಗಬಾರದು. ಬೇರೆ ಆಯ್ಕೆ ಮಾಡಿ."
                ))
                return {"destination": None}
            return {"destination": value.strip().title()}
        dispatcher.utter_message(text=(
            "Unknown destination station. Please provide a valid station name.\n"
            "ಗೊತ್ತಿಲ್ಲದ ಗಮ್ಯ ಸ್ಟೇಷನ್. ಸರಿಯಾದ ಸ್ಟೇಷನ್ ಹೇಳಿ."
        ))
        return {"destination": None}

    def validate_date_time(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Parse natural language date/time using python-dateutil.
        Supports phrases like 'today 6 pm', 'tomorrow 9:30 am', or explicit datetimes.
        Returns a normalized string 'YYYY-MM-DD HH:MM'.
        """
        if not value or len(value.strip()) < 3:
            dispatcher.utter_message(text=(
                "Please provide a valid time, e.g., 'today 6 pm' or 'tomorrow 9:30 am'.\n"
                "ದಯವಿಟ್ಟು ಸರಿಯಾದ ಸಮಯ ನೀಡಿ, ಉದಾ: 'ಇಂದು ಸಂಜೆ 6' ಅಥವಾ 'ನಾಳೆ ಬೆಳಗ್ಗೆ 9:30'."
            ))
            return {"date_time": None}

        text = value.strip()
        now = datetime.now()
        # Lightweight helpers for common English keywords
        lowered = text.lower()
        try_text = text
        if "tomorrow" in lowered:
            tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")
            try_text = lowered.replace("tomorrow", tomorrow_str)
        elif "today" in lowered:
            today_str = now.strftime("%Y-%m-%d")
            try_text = lowered.replace("today", today_str)

        try:
            dt = dateparser.parse(try_text, fuzzy=True, default=now)
            if not dt:
                raise ValueError("Could not parse date/time")
            # Normalize to minute precision
            normalized = dt.strftime("%Y-%m-%d %H:%M")
            return {"date_time": normalized}
        except Exception:
            dispatcher.utter_message(text=(
                "Couldn't understand the time. Try formats like '2025-10-17 18:00' or 'today 6 pm'.\n"
                "ಸಮಯವನ್ನು ಅರ್ಥಮಾಡಿಕೊಳ್ಳಲಾಗಲಿಲ್ಲ. '2025-10-17 18:00' ಅಥವಾ 'ಇಂದು ಸಂಜೆ 6' ರೀತಿಯಲ್ಲಿ ನೀಡಿ."
            ))
            return {"date_time": None}

    def validate_seats(
        self,
        value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        try:
            n = int(str(value).strip())
            if 1 <= n <= 6:
                return {"seats": n}
        except Exception:
            pass
        dispatcher.utter_message(text=(
            "Seats must be a number between 1 and 6.\n"
            "ಸೀಟುಗಳ ಸಂಖ್ಯೆ 1 ರಿಂದ 6 ನಡುವೆ ಇರಬೇಕು."
        ))
        return {"seats": None}

class ActionSubmitTicketForm(Action):
    def name(self) -> Text:
        return "action_submit_ticket_form"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[Text, Any]]:
        source = tracker.get_slot("source")
        destination = tracker.get_slot("destination")
        date_time = tracker.get_slot("date_time")
        seats_slot = tracker.get_slot("seats")
        try:
            seats = int(seats_slot) if seats_slot is not None else 1
        except Exception:
            seats = 1

        # Acknowledge submission and inform user we're checking availability
        try:
            dispatcher.utter_message(response="utter_submit")
        except Exception:
            # Fallback text if template resolution fails for any reason
            dispatcher.utter_message(text=(
                f"Noted. Booking from {source} to {destination} at {date_time} for {seats} seat(s). I will now check availability.\n"
                f"ಗಮನಿಸಲಾಗಿದೆ. {source} ಇಂದ {destination} ಗೆ {date_time} ಸಮಯಕ್ಕೆ {seats} ಸೀಟು(ಗಳು)ಗಾಗಿ ಪರಿಶೀಲಿಸುತ್ತಿದ್ದೇನೆ."
            ))

        # Availability check
        key = _timeslot_key(source, destination, date_time or "")
        available = _get_availability(key)
        if seats > available:
            dispatcher.utter_message(
                text=(
                    f"Sorry, only {available} seat(s) left for {source} → {destination} at {date_time}. Please reduce seats or pick another time.\n"
                    f"ಕ್ಷಮಿಸಿ, {date_time} ಸಮಯದಲ್ಲಿ {source} → {destination} ಮಾರ್ಗದಲ್ಲಿ {available} ಸೀಟು(ಗಳು) ಮಾತ್ರ ಉಳಿದಿವೆ. ದಯವಿಟ್ಟು ಸೀಟುಗಳನ್ನು ಕಡಿಮೆ ಮಾಡಿ ಅಥವಾ ಬೇರೆ ಸಮಯ ಆಯ್ಕೆಮಾಡಿ."
                )
            )
            return []

        dispatcher.utter_message(
            text=(
                f"Seats available! Proceeding to payment for {seats} seat(s).\n"
                f"ಸೀಟುಗಳು ಲಭ್ಯವಿವೆ! {seats} ಸೀಟು(ಗಳು)ಗಾಗಿ ಪಾವತಿಗೆ ಮುಂದುವರೆಯುತ್ತೇನೆ."
            )
        )

        # Mock payment simulation (85% success)
        success = random.random() < 0.85
        txn_ref = f"BMRC-{int(time.time())}-{random.randint(1000,9999)}"
        if not success:
            dispatcher.utter_message(
                text=(
                    f"Payment failed (ref: {txn_ref}). No amount was charged. Please try again.\n"
                    f"ಪಾವತಿ ವಿಫಲವಾಗಿದೆ (ಉಲ್ಲೇಖ: {txn_ref}). ಯಾವುದೇ ಹಣ ಕಡಿತವಾಗಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ."
                )
            )
            return []

        # Deduct seats on success and confirm
        _update_availability(key, -seats)
        remaining = _get_availability(key)
        # Generate QR ticket
        tickets_dir = os.path.join(os.getcwd(), "tickets")
        _ensure_dir(tickets_dir)
        payload = _build_ticket_payload(txn_ref, source, destination, date_time or "", seats)
        qr_path = os.path.join(tickets_dir, f"{txn_ref}.png")
        qr_file = _make_qr_image(payload, qr_path)

        # Persist booking stub (best-effort, no PII)
        try:
            init_db()
            save_booking(txn_ref, source or "", destination or "", (date_time or ""), int(seats), int(time.time()))
        except Exception:
            pass

        msg = (
            f"Payment successful! Ref: {txn_ref}. Booking confirmed: {source} → {destination} at {date_time}, {seats} seat(s). Remaining seats: {remaining}.\n"
            f"QR ticket saved: {qr_file or 'install qrcode to enable image'}\n"
            f"ಪಾವತಿ ಯಶಸ್ವಿಯಾಗಿದೆ! ಉಲ್ಲೇಖ: {txn_ref}. ಬುಕಿಂಗ್ ದೃಢವಾಗಿದೆ: {source} → {destination} {date_time}, {seats} ಸೀಟು(ಗಳು). ಉಳಿದ ಸೀಟುಗಳು: {remaining}.\n"
            f"QR ಟಿಕೆಟ್: {qr_file or 'ಚಿತ್ರಕ್ಕಾಗಿ qrcode ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡಿ'}"
        )
        dispatcher.utter_message(text=msg)
        return []


class ActionCheckBooking(Action):
    def name(self) -> Text:
        return "action_check_booking"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[Text, Any]]:
        ref = tracker.get_slot("booking_ref")
        if not ref:
            dispatcher.utter_message(text=(
                "Please provide your booking reference (e.g., BMRC-... ).\n"
                "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಬುಕಿಂಗ್ ಉಲ್ಲೇಖ ಸಂಖ್ಯೆ ನೀಡಿ (ಉದಾ., BMRC-...)."
            ))
            return []

        try:
            init_db()
            bk = get_booking(str(ref))
        except Exception as e:
            dispatcher.utter_message(text=(
                f"Couldn't access booking store. Try again later.\nError: {e}"
            ))
            return []

        if not bk:
            dispatcher.utter_message(text=(
                "No booking found for that reference.\n"
                "ಆ ಉಲ್ಲೇಖ ಸಂಖ್ಯೆಗೆ ಯಾವುದೇ ಬುಕಿಂಗ್ ಸಿಗಲಿಲ್ಲ."
            ))
            return []

        dispatcher.utter_message(text=(
            f"Booking {bk.ref}: {bk.source} → {bk.destination} at {bk.at}, seats: {bk.seats}.\n"
            f"ಬುಕಿಂಗ್ {bk.ref}: {bk.source} → {bk.destination} {bk.at}, ಸೀಟುಗಳು: {bk.seats}."
        ))
        return []
