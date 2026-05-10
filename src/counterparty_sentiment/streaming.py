"""Streaming helpers for rolling counterparty sentiment aggregation."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field

from .analyzer import SentimentAnalyzer
from .models import SentimentResult, TextEvent


@dataclass(frozen=True)
class CounterpartySnapshot:
    """Rolling sentiment state for a counterparty."""

    counterparty: str
    events: int
    average_score: float
    latest_label: str
    risk_flags: tuple[str, ...]
    dimension_scores: dict[str, float] = field(default_factory=dict)
    latest_severity: str = "low"


class SentimentStream:
    """Analyze events and maintain rolling windows per counterparty."""

    def __init__(self, analyzer: SentimentAnalyzer | None = None, window_size: int = 25) -> None:
        if window_size <= 0:
            raise ValueError("window_size must be positive")
        self.analyzer = analyzer or SentimentAnalyzer()
        self.window_size = window_size
        self._windows: dict[str, deque[SentimentResult]] = defaultdict(lambda: deque(maxlen=window_size))

    def process(self, event: TextEvent) -> SentimentResult:
        """Analyze an event and update its counterparty rolling window."""
        result = self.analyzer.analyze(event)
        self._windows[event.counterparty].append(result)
        return result

    def process_many(self, events: Iterable[TextEvent]) -> Iterator[SentimentResult]:
        """Yield sentiment results as events are processed."""
        for event in events:
            yield self.process(event)

    def snapshot(self, counterparty: str) -> CounterpartySnapshot | None:
        """Return the current rolling snapshot for a counterparty."""
        window = self._windows.get(counterparty)
        if not window:
            return None
        average_score = sum(result.score for result in window) / len(window)
        risk_flags = tuple(sorted({flag for result in window for flag in result.risk_flags}))
        dimension_names = sorted({dimension for result in window for dimension in result.dimension_scores})
        dimension_scores = {
            dimension: round(sum(result.dimension_scores.get(dimension, 0.0) for result in window) / len(window), 4)
            for dimension in dimension_names
        }
        return CounterpartySnapshot(
            counterparty=counterparty,
            events=len(window),
            average_score=round(average_score, 4),
            latest_label=window[-1].label,
            risk_flags=risk_flags,
            dimension_scores=dimension_scores,
            latest_severity=window[-1].severity,
        )
