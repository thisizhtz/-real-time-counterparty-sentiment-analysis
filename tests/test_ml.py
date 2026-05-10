import pytest

from counterparty_sentiment.ml import OptionalFinBERTScorer


def test_optional_finbert_reports_missing_dependency_cleanly():
    with pytest.raises(RuntimeError, match="FinBERT mode requires optional dependency"):
        OptionalFinBERTScorer()
