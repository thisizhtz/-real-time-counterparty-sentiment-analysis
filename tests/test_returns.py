from counterparty_sentiment.models import TextEvent
from counterparty_sentiment.returns import calculate_event_returns


def test_calculate_event_returns_uses_next_trading_day_and_horizons():
    event = TextEvent(counterparty="Apple", ticker="AAPL", text="Apple beat estimates.", timestamp=__import__("datetime").datetime.fromisoformat("2026-01-03T12:00:00+00:00"))
    prices = [
        ("2026-01-02", 100),
        ("2026-01-05", 102),
        ("2026-01-06", 104),
        ("2026-01-07", 106),
        ("2026-01-08", 108),
        ("2026-01-09", 110),
    ]
    benchmark = [(day, close) for day, close in [("2026-01-02", 100), ("2026-01-05", 101), ("2026-01-06", 102), ("2026-01-07", 103), ("2026-01-08", 104), ("2026-01-09", 105)]]

    returns = calculate_event_returns(event, prices, benchmark_prices=benchmark, horizons=(1, 3))

    assert returns["event_trading_date"] == "2026-01-05"
    assert returns["forward_return_1d"] == round(104 / 102 - 1, 6)
    assert returns["forward_return_3d"] == round(108 / 102 - 1, 6)
    assert returns["pre_event_return_1d"] == round(102 / 100 - 1, 6)
    assert returns["abnormal_return_1d"] == round((104 / 102 - 1) - (102 / 101 - 1), 6)
