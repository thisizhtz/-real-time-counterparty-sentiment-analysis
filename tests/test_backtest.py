from counterparty_sentiment.backtest import backtest_results, generate_signal, prepare_signal_rows


def test_generate_signal_thresholds():
    assert generate_signal(0.2) == 1
    assert generate_signal(-0.2) == -1
    assert generate_signal(0.01) == 0


def test_backtest_metrics_and_confusion_table():
    rows = [
        {"score": 0.4, "label": "positive", "returns": {"forward_return_1d": 0.02}},
        {"score": -0.5, "label": "negative", "returns": {"forward_return_1d": -0.03}},
        {"score": 0.3, "label": "positive", "returns": {"forward_return_1d": -0.01}},
        {"score": 0.0, "label": "neutral", "returns": {"forward_return_1d": 0.01}},
    ]

    prepared = prepare_signal_rows(rows)
    metrics = backtest_results(rows)

    assert prepared[0]["signal"] == 1
    assert prepared[1]["strategy_return"] == 0.03
    assert metrics["n_events"] == 4
    assert metrics["n_trades"] == 3
    assert metrics["hit_rate"] == round(2 / 3, 6)
    assert metrics["cumulative_return"] > 0
    assert metrics["confusion_table"]["positive"]["up"] == 1
    assert metrics["confusion_table"]["positive"]["down"] == 1
