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


def test_systemic_private_credit_warning_is_material_negative_signal():
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze(
        TextEvent(
            counterparty="Global Private Credit Market",
            source="reuters",
            text="The Financial Stability Board warned that growing links between banks and private credit firms could amplify systemic financial risks.",
        )
    )

    assert result.label == "negative"
    assert result.score < -0.5
    assert result.severity == "high"
    assert result.dimension_scores["systemic"] > 0.8
    assert "systemic financial risks" in result.matched_negative_terms
    assert "systemic_risk" in result.risk_flags
    assert "private_credit_exposure" in result.risk_flags


def test_result_serializes_dimension_scores_and_explanation():
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze(TextEvent(counterparty="Acme", text="Acme faces severe liquidity squeeze and distress."))
    payload = result.to_dict()

    assert "dimension_scores" in payload
    assert payload["severity"] in {"medium", "high"}
    assert payload["explanation"]
