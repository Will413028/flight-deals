"""Fetch cheapest round-trip prices per departure date from Google Flights via fli.

fli reverse-engineers Google Flights' internal calendar endpoint; when Google
changes it, upgrade the `flights` package.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from fli.core import build_date_search_segments, parse_max_stops, resolve_airport
from fli.models import DateSearchFilters, PassengerInfo
from fli.search import SearchDates
from fli.search._concurrency import configure_concurrency

ORIGIN = "TPE"

# fli splits a long range into 61-day chunks fetched in parallel; serialize them to keep
# the request rate low (private API of flights 0.9.0, pinned).
configure_concurrency(1)


@dataclass(frozen=True)
class DatePrice:
    depart: date
    ret: date
    price: int


def search(destination: str, days: int, start: date, end: date) -> list[DatePrice]:
    """Round-trip, economy, at most one stop, prices in TWD."""
    origins = [resolve_airport(ORIGIN)]
    dests = [resolve_airport(c.strip()) for c in destination.split(",")]
    segments, trip_type = build_date_search_segments(
        origin=origins,
        destination=dests,
        start_date=start.isoformat(),
        trip_duration=days,
        is_round_trip=True,
    )
    filters = DateSearchFilters(
        trip_type=trip_type,
        passenger_info=PassengerInfo(adults=1),
        flight_segments=segments,
        stops=parse_max_stops("ONE_STOP"),
        from_date=start.isoformat(),
        to_date=end.isoformat(),
        duration=days,
    )
    results = SearchDates().search(filters, currency="TWD") or []
    out = []
    for r in results:
        if r.currency and r.currency.upper() != "TWD":
            raise ValueError(f"expected TWD prices, got {r.currency}")
        dep = r.date[0].date()
        ret = r.date[1].date() if len(r.date) > 1 else dep + timedelta(days=days)
        out.append(DatePrice(dep, ret, round(r.price)))
    return out


def booking_link(destination: str, depart: date, ret: date) -> str:
    """Google Flights search page for the exact itinerary."""
    dest = destination.split(",")[0]
    q = f"Flights from {ORIGIN} to {dest} on {depart} through {ret}"
    return "https://www.google.com/travel/flights?hl=zh-TW&curr=TWD&q=" + q.replace(" ", "%20")
