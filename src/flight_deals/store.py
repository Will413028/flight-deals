"""SQLite price history and alert log.

A path ending in `.sql` is kept as a text dump instead of a database file: loaded into
memory on open, written back on close. CI stores that dump in git, where row-ordered
text diffs stay small and a binary database file would not.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

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
    def __init__(self, path: str, readonly: bool = False):
        self.readonly = readonly  # dry runs: changes stay in memory and are never written
        self.dump = Path(path) if path.endswith(".sql") else None
        self.db = sqlite3.connect(":memory:" if self.dump else path)
        if self.dump and self.dump.exists():
            self.db.executescript(self.dump.read_text())
        self.db.executescript(SCHEMA)

    def prune(self, before: datetime) -> None:
        """Drop rows no rule can read any more (all rules look back at most one window)."""
        self.db.execute("DELETE FROM prices WHERE seen_at < ?", (before.isoformat(),))
        self.db.execute("DELETE FROM alerts WHERE sent_at < ?", (before.isoformat(),))

    def close(self) -> None:
        self.commit()
        self.db.close()

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
        """Make everything so far durable; for a dump, rewrite it atomically."""
        if self.readonly:
            return
        self.db.commit()
        if self.dump:
            tmp = self.dump.with_suffix(".sql.tmp")
            tmp.write_text("\n".join(self.db.iterdump()) + "\n")
            os.replace(tmp, self.dump)
