"""flight-deals: run | test-notify | check-destinations"""

from __future__ import annotations

import argparse
import os
import random
import sys
import time
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from flight_deals import fetch, telegram
from flight_deals.deal import DEFAULT, Quote, Reason, evaluate
from flight_deals.destinations import DESTINATIONS
from flight_deals.store import Store

TZ = ZoneInfo("Asia/Taipei")
HORIZON_MONTHS = 12


def search_window(today: date) -> tuple[date, date]:
    """Tomorrow through the last day of the 12th month ahead (current month counts as the 1st).

    The end lands on a month boundary so the last month's series always covers the
    same dates; a rolling end would grow that month daily and fake price drops.
    """
    y, m = divmod(today.month - 1 + HORIZON_MONTHS, 12)
    return today + timedelta(days=1), date(today.year + y, m + 1, 1) - timedelta(days=1)


def _env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        sys.exit(f"missing environment variable {name}")
    return v


def monthly_cheapest(destination: str, prices: list[fetch.DatePrice], now: datetime) -> list[Quote]:
    best: dict[str, fetch.DatePrice] = {}
    for p in prices:
        m = p.depart.strftime("%Y-%m")
        if m not in best or p.price < best[m].price:
            best[m] = p
    return [
        Quote(destination, m, p.price, p.depart.isoformat(), p.ret.isoformat(), now)
        for m, p in sorted(best.items())
    ]


def format_alert(name: str, q: Quote, median: int) -> str:
    off = round((1 - q.price / median) * 100)
    return (
        f"✈️ 桃園 → {name}（{q.destination}）\n"
        f"{q.depart} 去／{q.ret} 回\n"
        f"NT${q.price:,}（平常約 NT${median:,}，便宜 {off}%）\n"
        f"{fetch.booking_link(q.destination, date.fromisoformat(q.depart), date.fromisoformat(q.ret))}"
    )


def cmd_run(args: argparse.Namespace) -> int:
    notify = not args.dry_run
    token = _env("TELEGRAM_BOT_TOKEN") if notify else ""
    chat = _env("TELEGRAM_CHAT_ID") if notify else ""
    store = Store(args.db)
    now = datetime.now(TZ).replace(microsecond=0)
    start, end = search_window(now.date())
    dests = DESTINATIONS[: args.limit] if args.limit else DESTINATIONS
    ok = failed = saved = alerts = notify_failed = 0
    for i, d in enumerate(dests):
        if i:
            time.sleep(args.delay + random.uniform(0, args.delay))
        try:
            prices = fetch.search(d.code, d.days, start, end)
        except Exception as e:  # noqa: BLE001 — one bad destination must not stop the run
            failed += 1
            print(f"FAIL {d.code}: {type(e).__name__}: {e}", file=sys.stderr)
            continue
        ok += 1
        for q in monthly_cheapest(d.code, prices, now):
            dec = evaluate(q, store.history(q, DEFAULT.window), store.last_alert_price(q, DEFAULT.window))
            store.save_price(q)
            saved += 1
            if dec.reason is not Reason.ALERT:
                continue
            msg = format_alert(d.name, q, dec.median)
            if not notify:  # dry run: never record the alert, or it would suppress the real one
                print(msg + "\n")
                alerts += 1
                continue
            try:
                telegram.send(token, chat, msg)
            except Exception as e:  # noqa: BLE001 — retry next run instead of aborting this one
                notify_failed += 1
                print(f"NOTIFY FAIL {q.key}: {e}", file=sys.stderr)
                continue
            alerts += 1
            store.save_alert(q)
            store.commit()  # record the sent alert at once so a crash cannot resend it
        store.commit()
    store.prune(now - DEFAULT.window - timedelta(days=1))
    store.close()
    print(
        f"destinations ok={ok} failed={failed} prices_saved={saved} "
        f"alerts={alerts} notify_failed={notify_failed}"
    )
    return 1 if ok == 0 else 0


def cmd_test_notify(_: argparse.Namespace) -> int:
    telegram.send(_env("TELEGRAM_BOT_TOKEN"), _env("TELEGRAM_CHAT_ID"), "flight-deals 測試通知 ✅")
    print("sent")
    return 0


def cmd_check_destinations(_: argparse.Namespace) -> int:
    bad = []
    for d in DESTINATIONS:
        for c in (x.strip() for x in d.code.split(",")):
            try:
                fetch.resolve_airport(c)
            except Exception:  # noqa: BLE001 — any parse error means unknown code
                bad.append(c)
    print(f"destinations={len(DESTINATIONS)} unknown_codes={bad}")
    return 1 if bad else 0


def main() -> int:
    p = argparse.ArgumentParser(prog="flight-deals")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="fetch prices, store them, alert on deals")
    r.add_argument("--db", default=os.environ.get("FLIGHT_DEALS_DB", "prices.db"))
    r.add_argument("--delay", type=float, default=1.0, help="base seconds between destinations")
    r.add_argument("--limit", type=int, default=0, help="only the first N destinations")
    r.add_argument("--dry-run", action="store_true", help="print alerts instead of sending")
    r.set_defaults(fn=cmd_run)
    sub.add_parser("test-notify").set_defaults(fn=cmd_test_notify)
    sub.add_parser("check-destinations").set_defaults(fn=cmd_check_destinations)
    args = p.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
