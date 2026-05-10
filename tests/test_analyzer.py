from counterparty_sentiment import SentimentAnalyzer, TextEvent


def test_positive_financial_signal_is_detected():
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze(TextEvent(counterparty="Acme Bank", text="Acme was upgraded and remains stable."))

    assert result.label == "positive"
    assert result.score > 0
    assert "upgraded" in result.matched_positive_terms


def test_negative_risk_signal_sets_flags():
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze(
        TextEvent(counterparty="Beta Fund", text="Beta Fund missed payment deadlines and faces default risk.")
    )

    assert result.label == "negative"
    assert result.score < 0
    assert "missed payment" in result.matched_negative_terms
    assert "payment_stress" in result.risk_flags
    assert "credit_default" in result.risk_flags


def test_negation_reduces_negative_score():
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze(TextEvent(counterparty="Gamma Ltd", text="Gamma is not in default and is stable."))

    assert result.score >= 0
