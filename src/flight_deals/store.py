"""SQLite price history and alert log."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta

from flight_deals.deal import Observation, Quote

SCHEMA = """
CREATE TABLE IF NOT EXISTS prices (
    destination TEXT NOT NULL,
    month       TEXT NOT NULL,
    price       INTEGER NOT NULL,
    depart      TEXT NOT NULL,
    ret         TEXT NOT NULL,
    seen_at     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS prices_series ON prices (destination, month, seen_at);
CREATE TABLE IF NOT EXISTS alerts (
    destination TEXT NOT NULL,
    month       TEXT NOT NULL,
    price       INTEGER NOT NULL,
    sent_at     TEXT NOT NULL
);
"""


class Store:
    def __init__(self, path: str):
        self.db = sqlite3.connect(path)
        self.db.executescript(SCHEMA)

    def history(self, q: Quote, window: timedelta) -> list[Observation]:
        since = (q.seen_at - window).isoformat()
        rows = self.db.execute(
            "SELECT price, seen_at FROM prices WHERE destination=? AND month=? AND seen_at>=? AND seen_at<?",
            (q.destination, q.month, since, q.seen_at.isoformat()),
        )
        return [Observation(p, datetime.fromisoformat(s)) for p, s in rows]

    def last_alert_price(self, q: Quote, window: timedelta) -> int | None:
        """Most recent alert in the window; older alerts no longer suppress."""
        since = (q.seen_at - window).isoformat()
        row = self.db.execute(
            "SELECT price FROM alerts WHERE destination=? AND month=? AND sent_at>=? ORDER BY sent_at DESC LIMIT 1",
            (q.destination, q.month, since),
        ).fetchone()
        return row[0] if row else None

    def save_price(self, q: Quote) -> None:
        self.db.execute(
            "INSERT INTO prices VALUES (?,?,?,?,?,?)",
            (q.destination, q.month, q.price, q.depart, q.ret, q.seen_at.isoformat()),
        )

    def save_alert(self, q: Quote) -> None:
        self.db.execute(
            "INSERT INTO alerts VALUES (?,?,?,?)",
            (q.destination, q.month, q.price, q.seen_at.isoformat()),
        )

    def commit(self) -> None:
        self.db.commit()
