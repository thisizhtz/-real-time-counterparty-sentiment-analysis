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


def test_window_size_limits_snapshot_events():
    stream = SentimentStream(window_size=1)
    stream.process(TextEvent(counterparty="Acme", text="Acme is stable."))
    stream.process(TextEvent(counterparty="Acme", text="Acme default risk increased."))

    snapshot = stream.snapshot("Acme")

    assert snapshot is not None
    assert snapshot.events == 1
    assert snapshot.latest_label == "negative"
