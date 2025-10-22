from __future__ import annotations
import os
import sqlite3
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

DB_PATH = os.path.join(os.getcwd(), "data", "booking.db")


def _ensure_parent() -> None:
    Path(os.path.dirname(DB_PATH)).mkdir(parents=True, exist_ok=True)


def get_conn() -> sqlite3.Connection:
    _ensure_parent()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                ref TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                destination TEXT NOT NULL,
                at TEXT NOT NULL,
                seats INTEGER NOT NULL,
                created_at INTEGER NOT NULL
            )
            """
        )
        conn.commit()


def save_booking(ref: str, source: str, destination: str, at: str, seats: int, created_at: int) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO bookings(ref, source, destination, at, seats, created_at)
            VALUES(?,?,?,?,?,?)
            """,
            (ref, source, destination, at, seats, created_at),
        )
        conn.commit()


@dataclass
class Booking:
    ref: str
    source: str
    destination: str
    at: str
    seats: int
    created_at: int


def get_booking(ref: str) -> Optional[Booking]:
    with get_conn() as conn:
        cur = conn.execute("SELECT ref, source, destination, at, seats, created_at FROM bookings WHERE ref=?", (ref,))
        row = cur.fetchone()
        if not row:
            return None
        return Booking(
            ref=row["ref"],
            source=row["source"],
            destination=row["destination"],
            at=row["at"],
            seats=int(row["seats"]),
            created_at=int(row["created_at"]),
        )


def purge_older_than(seconds: int) -> int:
    """Delete bookings older than 'seconds'. Returns rows affected."""
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM bookings WHERE created_at < strftime('%s','now') - ?", (seconds,))
        conn.commit()
        return cur.rowcount
