"""Decide whether a fare is cheap enough to alert on. Pure logic, no I/O."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from statistics import median


@dataclass(frozen=True)
class Quote:
    """Cheapest round-trip fare seen for one destination and departure month."""

    destination: str  # e.g. "NRT,HND"
    month: str  # departure month, "2027-03"
    price: int  # TWD
    depart: str  # YYYY-MM-DD
    ret: str  # YYYY-MM-DD
    seen_at: datetime

    @property
    def key(self) -> str:
        return f"{self.destination}|{self.month}"


@dataclass(frozen=True)
class Observation:
    price: int
    seen_at: datetime


@dataclass(frozen=True)
class Config:
    window: timedelta = timedelta(days=30)  # baseline history window
    min_history: timedelta = timedelta(days=7)  # oldest observation must be this old
    discount: float = 0.25  # alert when price <= median * (1 - discount)
    re_alert_drop: float = 0.05  # re-alert only after a further drop


DEFAULT = Config()  # confirmed by Will on 2026-11-05


class Reason(str, Enum):
    ALERT = "alert"
    NOT_ENOUGH_HISTORY = "not_enough_history"
    NOT_CHEAP_ENOUGH = "not_cheap_enough"
    ALREADY_ALERTED = "already_alerted"


@dataclass(frozen=True)
class Decision:
    reason: Reason
    median: int = 0  # baseline used; 0 when none was computed


def evaluate(
    q: Quote,
    history: list[Observation],
    last_alert_price: int | None,
    cfg: Config = DEFAULT,
) -> Decision:
    """history: earlier observations of the same series, q itself excluded."""
    in_window = [
        o for o in history if timedelta(0) <= q.seen_at - o.seen_at <= cfg.window
    ]
    if not in_window:
        return Decision(Reason.NOT_ENOUGH_HISTORY)
    oldest = min(o.seen_at for o in in_window)
    if q.seen_at - oldest < cfg.min_history:
        return Decision(Reason.NOT_ENOUGH_HISTORY)
    med = int(median(o.price for o in in_window))
    if q.price > med * (1 - cfg.discount):
        return Decision(Reason.NOT_CHEAP_ENOUGH, med)
    if last_alert_price is not None and q.price > last_alert_price * (1 - cfg.re_alert_drop):
        return Decision(Reason.ALREADY_ALERTED, med)
    return Decision(Reason.ALERT, med)
