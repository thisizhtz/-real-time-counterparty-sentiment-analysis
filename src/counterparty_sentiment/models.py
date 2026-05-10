"""Typed data models for sentiment analysis inputs and outputs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class TextEvent:
    """A single text observation about one counterparty."""

    counterparty: str
    text: str
    source: str = "unknown"
    event_id: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "TextEvent":
        """Create an event from a dictionary, accepting ISO-8601 timestamps."""
        raw_timestamp = payload.get("timestamp")
        if isinstance(raw_timestamp, datetime):
            timestamp = raw_timestamp
        elif isinstance(raw_timestamp, str) and raw_timestamp:
            timestamp = datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))
        else:
            timestamp = datetime.now(timezone.utc)

        return cls(
            counterparty=str(payload["counterparty"]).strip(),
            text=str(payload["text"]).strip(),
            source=str(payload.get("source", "unknown")).strip() or "unknown",
            event_id=str(payload["event_id"]) if payload.get("event_id") is not None else None,
            timestamp=timestamp,
        )


@dataclass(frozen=True)
class SentimentResult:
    """Normalized sentiment output for a counterparty text event."""

    event: TextEvent
    score: float
    label: str
    confidence: float
    matched_positive_terms: tuple[str, ...] = ()
    matched_negative_terms: tuple[str, ...] = ()
    risk_flags: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        event_dict = asdict(self.event)
        event_dict["timestamp"] = self.event.timestamp.isoformat()
        return {
            "event": event_dict,
            "score": self.score,
            "label": self.label,
            "confidence": self.confidence,
            "matched_positive_terms": list(self.matched_positive_terms),
            "matched_negative_terms": list(self.matched_negative_terms),
            "risk_flags": list(self.risk_flags),
        }
