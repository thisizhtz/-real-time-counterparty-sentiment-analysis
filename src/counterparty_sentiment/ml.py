"""Optional ML sentiment extension points.

The core project intentionally has no heavy ML dependencies.  This module provides a
small protocol-compatible wrapper so users can plug in FinBERT or another
transformer at runtime while keeping lexicon-only mode as the default fallback.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class MLSentimentScore:
    label: str
    score: float
    confidence: float
    model_name: str


class MLSentimentModel(Protocol):
    def predict(self, text: str) -> MLSentimentScore:
        """Return a normalized sentiment score in [-1, 1]."""


class OptionalFinBERTScorer:
    """Lazy optional FinBERT adapter.

    The adapter imports ``transformers`` only when instantiated. If the optional
    dependency is missing, callers receive a clear error and can continue using
    the rule-based analyzer.
    """

    def __init__(self, model_name: str = "ProsusAI/finbert") -> None:
        try:
            from transformers import pipeline
        except ImportError as exc:
            raise RuntimeError(
                "FinBERT mode requires optional dependency 'transformers'. "
                "Install it separately or use the default lexicon-only analyzer."
            ) from exc
        self.model_name = model_name
        self._pipeline = pipeline("text-classification", model=model_name)

    def predict(self, text: str) -> MLSentimentScore:
        raw = self._pipeline(text[:4096])[0]
        label = str(raw["label"]).lower()
        confidence = float(raw["score"])
        score = confidence if label == "positive" else -confidence if label == "negative" else 0.0
        return MLSentimentScore(label=label, score=score, confidence=confidence, model_name=self.model_name)
