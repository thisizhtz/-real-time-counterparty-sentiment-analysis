from datetime import datetime, timezone

from counterparty_sentiment import SentimentStream, TextEvent


def test_stream_snapshot_rolls_up_counterparty_state():
    stream = SentimentStream(window_size=2)
    stream.process(TextEvent(counterparty="Acme", text="Acme is stable."))
    stream.process(TextEvent(counterparty="Acme", text="Acme faces a lawsuit and downgrade."))

    snapshot = stream.snapshot("Acme")

    assert snapshot is not None
    assert snapshot.counterparty == "Acme"
    assert snapshot.events == 2
    assert snapshot.latest_label == "negative"
    assert "credit" in snapshot.dimension_scores


def test_window_size_limits_snapshot_events():
    stream = SentimentStream(window_size=1)
    stream.process(TextEvent(counterparty="Acme", text="Acme is stable."))
    stream.process(TextEvent(counterparty="Acme", text="Acme default risk increased."))

    snapshot = stream.snapshot("Acme")

    assert snapshot is not None
    assert snapshot.events == 1
    assert snapshot.latest_label == "negative"


def test_temporal_snapshot_detects_deteriorating_escalation():
    stream = SentimentStream(window_size=5)
    stream.process(TextEvent(counterparty="HSBC", text="HSBC remains stable.", timestamp=datetime(2026, 5, 1, tzinfo=timezone.utc)))
    stream.process(TextEvent(counterparty="HSBC", text="HSBC faces downgrade risk.", timestamp=datetime(2026, 5, 2, tzinfo=timezone.utc)))
    stream.process(TextEvent(counterparty="HSBC", text="HSBC missed payment and issued a default warning.", timestamp=datetime(2026, 5, 3, tzinfo=timezone.utc)))

    snapshot = stream.snapshot("HSBC", as_of=datetime(2026, 5, 3, 12, tzinfo=timezone.utc))

    assert snapshot is not None
    assert snapshot.trend == "deteriorating"
    assert snapshot.escalation_level in {"watch", "escalate"}
    assert snapshot.rolling_volatility > 0
    assert "credit_risk" in snapshot.top_risk_flags
