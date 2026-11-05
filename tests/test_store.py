from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from flight_deals.deal import Quote
from flight_deals.store import Store

NOW = datetime(2026, 11, 5, 12, tzinfo=ZoneInfo("Asia/Taipei"))


def q(price: int, seen_at: datetime) -> Quote:
    return Quote("KIX", "2027-03", price, "2027-03-01", "2027-03-06", seen_at)


def test_sql_dump_round_trip_and_prune(tmp_path):
    path = str(tmp_path / "prices.sql")
    s = Store(path)
    s.save_price(q(9000, NOW - timedelta(days=40)))
    s.save_price(q(8000, NOW - timedelta(days=2)))
    s.save_alert(q(8000, NOW - timedelta(days=2)))
    s.prune(NOW - timedelta(days=31))
    s.close()

    reopened = Store(path)
    probe = q(7000, NOW)
    assert [o.price for o in reopened.history(probe, timedelta(days=60))] == [8000]
    assert reopened.last_alert_price(probe, timedelta(days=30)) == 8000


def test_committed_alert_survives_without_close(tmp_path):
    path = str(tmp_path / "prices.sql")
    s = Store(path)
    s.save_alert(q(8000, NOW))
    s.commit()  # process dies here: close() never runs
    assert Store(path).last_alert_price(q(7000, NOW), timedelta(days=30)) == 8000


def test_readonly_store_writes_nothing(tmp_path):
    path = tmp_path / "prices.sql"
    s = Store(str(path), readonly=True)
    s.save_price(q(8000, NOW))
    s.close()
    assert not path.exists()
