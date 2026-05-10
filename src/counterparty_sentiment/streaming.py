"""Streaming helpers for temporal counterparty risk aggregation."""

from __future__ import annotations

import math
from collections import Counter, defaultdict, deque
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from .analyzer import SentimentAnalyzer
from .models import SentimentResult, TextEvent


@dataclass(frozen=True)
class CounterpartySnapshot:
    """Rolling and temporal risk state for a counterparty."""

    counterparty: str
    events: int
    average_score: float
    latest_label: str
    risk_flags: tuple[str, ...]
    dimension_scores: dict[str, float] = field(default_factory=dict)
    latest_severity: str = "low"
    rolling_volatility: float = 0.0
    event_frequency: float = 0.0
    last_24h_avg_score: float = 0.0
    last_7d_avg_score: float = 0.0
    trend: str = "stable"
    escalation_level: str = "normal"
    top_risk_flags: tuple[str, ...] = ()
    decayed_risk_score: float = 0.0

    def to_dict(self) -> dict[str, object]:
        return {
            "counterparty": self.counterparty,
            "events": self.events,
            "average_score": self.average_score,
            "latest_label": self.latest_label,
            "risk_flags": list(self.risk_flags),
            "dimension_scores": self.dimension_scores,
            "latest_severity": self.latest_severity,
            "rolling_volatility": self.rolling_volatility,
            "event_frequency": self.event_frequency,
            "last_24h_avg_score": self.last_24h_avg_score,
            "last_7d_avg_score": self.last_7d_avg_score,
            "trend": self.trend,
            "escalation_level": self.escalation_level,
            "top_risk_flags": list(self.top_risk_flags),
            "decayed_risk_score": self.decayed_risk_score,
        }


class SentimentStream:
    """Analyze events and maintain rolling temporal windows per counterparty."""

    def __init__(self, analyzer: SentimentAnalyzer | None = None, window_size: int = 100) -> None:
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

    def snapshot(self, counterparty: str, as_of: datetime | None = None) -> CounterpartySnapshot | None:
        """Return the current temporal risk snapshot for a counterparty."""
        window = self._windows.get(counterparty)
        if not window:
            return None
        now = as_of or max(result.event.timestamp for result in window)
        now = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
        results = list(window)
        scores = [result.adjusted_score if result.adjusted_score is not None else result.score for result in results]
        risk_flags = tuple(sorted({flag for result in results for flag in result.risk_flags}))
        top_risk_flags = tuple(flag for flag, _ in Counter(flag for result in results for flag in result.risk_flags).most_common(5))
        dimension_scores = _average_dimensions(results)
        last_24h = _filter_since(results, now, timedelta(hours=24))
        last_7d = _filter_since(results, now, timedelta(days=7))
        last_24h_avg = _average_score(last_24h)
        last_7d_avg = _average_score(last_7d)
        volatility = _volatility(scores)
        trend = _trend(results)
        decayed_risk_score = _decayed_risk_score(results, now)
        escalation_level = _escalation_level(results[-1], trend, decayed_risk_score, volatility)
        event_frequency = len(last_24h) / 24

        return CounterpartySnapshot(
            counterparty=counterparty,
            events=len(results),
            average_score=round(sum(scores) / len(scores), 4),
            latest_label=results[-1].label,
            risk_flags=risk_flags,
            dimension_scores=dimension_scores,
            latest_severity=results[-1].severity,
            rolling_volatility=round(volatility, 4),
            event_frequency=round(event_frequency, 4),
            last_24h_avg_score=round(last_24h_avg, 4),
            last_7d_avg_score=round(last_7d_avg, 4),
            trend=trend,
            escalation_level=escalation_level,
            top_risk_flags=top_risk_flags,
            decayed_risk_score=round(decayed_risk_score, 4),
        )


def _score(result: SentimentResult) -> float:
    return result.adjusted_score if result.adjusted_score is not None else result.score


def _filter_since(results: list[SentimentResult], now: datetime, delta: timedelta) -> list[SentimentResult]:
    cutoff = now.astimezone(timezone.utc) - delta
    return [result for result in results if result.event.timestamp.astimezone(timezone.utc) >= cutoff]


def _average_score(results: list[SentimentResult]) -> float:
    return sum(_score(result) for result in results) / len(results) if results else 0.0


def _average_dimensions(results: list[SentimentResult]) -> dict[str, float]:
    names = sorted({dimension for result in results for dimension in result.dimension_scores})
    return {
        dimension: round(sum(result.dimension_scores.get(dimension, 0.0) for result in results) / len(results), 4)
        for dimension in names
    }


def _volatility(scores: list[float]) -> float:
    if len(scores) < 2:
        return 0.0
    mean = sum(scores) / len(scores)
    return math.sqrt(sum((score - mean) ** 2 for score in scores) / (len(scores) - 1))


def _trend(results: list[SentimentResult]) -> str:
    if len(results) < 3:
        return "stable"
    midpoint = len(results) // 2
    older = _average_score(results[:midpoint])
    recent = _average_score(results[midpoint:])
    delta = recent - older
    if delta <= -0.12:
        return "deteriorating"
    if delta >= 0.12:
        return "improving"
    return "stable"


def _decayed_risk_score(results: list[SentimentResult], now: datetime) -> float:
    total_weight = 0.0
    weighted = 0.0
    for result in results:
        age_hours = max(0.0, (now - result.event.timestamp.astimezone(timezone.utc)).total_seconds() / 3600)
        weight = math.exp(-age_hours / (24 * 7))
        total_weight += weight
        weighted += max(0.0, -_score(result)) * weight
    return weighted / total_weight if total_weight else 0.0


def _escalation_level(result: SentimentResult, trend: str, decayed_risk_score: float, volatility: float) -> str:
    if result.severity == "high" or (trend == "deteriorating" and decayed_risk_score >= 0.35):
        return "escalate"
    if result.severity == "medium" or decayed_risk_score >= 0.25 or volatility >= 0.35:
        return "watch"
    return "normal"
