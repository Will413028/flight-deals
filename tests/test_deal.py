from datetime import datetime, timedelta

import pytest

from flight_deals.deal import DEFAULT, Observation, Quote, Reason, evaluate

NOW = datetime(2026, 11, 5, 12)


def history(days: int, price: int) -> list[Observation]:
    """One observation per day, the oldest `days` days ago."""
    return [Observation(price, NOW - timedelta(days=d)) for d in range(days, 0, -1)]


def quote(price: int) -> Quote:
    return Quote("NRT,HND", "2027-03", price, "2027-03-01", "2027-03-06", NOW)


@pytest.mark.parametrize(
    ("price", "hist", "last_alert", "want"),
    [
        pytest.param(7500, history(10, 10000), None, Reason.ALERT, id="25% below alerts"),
        pytest.param(8000, history(10, 10000), None, Reason.NOT_CHEAP_ENOUGH, id="20% below does not"),
        pytest.param(5000, history(6, 10000), None, Reason.NOT_ENOUGH_HISTORY, id="6 days history"),
        pytest.param(5000, history(7, 10000), None, Reason.ALERT, id="7 days history is enough"),
        pytest.param(5000, [], None, Reason.NOT_ENOUGH_HISTORY, id="no history"),
        pytest.param(7500, history(10, 10000), 7500, Reason.ALREADY_ALERTED, id="same price as last alert"),
        pytest.param(7200, history(10, 10000), 7500, Reason.ALREADY_ALERTED, id="4% below last alert"),
        pytest.param(7125, history(10, 10000), 7500, Reason.ALERT, id="5% below last alert re-alerts"),
        pytest.param(5000, history(40, 10000)[:5], None, Reason.NOT_ENOUGH_HISTORY, id="older than 30 days ignored"),
    ],
)
def test_evaluate(price, hist, last_alert, want):
    assert evaluate(quote(price), hist, last_alert, DEFAULT).reason == want


def test_median_resists_outlier():
    h = history(10, 10000)
    h[0] = Observation(100000, h[0].seen_at)  # one absurd spike must not raise the baseline
    d = evaluate(quote(7500), h, None)
    assert (d.reason, d.median) == (Reason.ALERT, 10000)


def test_search_window_ends_on_month_boundary():
    from datetime import date

    from flight_deals.cli import search_window

    assert search_window(date(2026, 11, 5)) == (date(2026, 11, 6), date(2027, 10, 31))
    assert search_window(date(2026, 12, 31)) == (date(2027, 1, 1), date(2027, 11, 30))
