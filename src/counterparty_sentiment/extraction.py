"""Structured event extraction for financial counterparty risk text."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .lexicons import EVENT_TYPE_PATTERNS

_AMOUNT_RE = re.compile(
    r"(?P<currency>\$|usd\s*)?\s*(?P<number>\d+(?:\.\d+)?)\s*(?P<unit>billion|bn|million|mn|m)?",
    re.IGNORECASE,
)
_PERCENT_RE = re.compile(r"(?P<number>\d+(?:\.\d+)?)\s*(?:%|percent|percentage points?)", re.IGNORECASE)
_MARKETS = ("private credit", "leveraged loan", "high yield", "commercial real estate", "crypto", "rates", "equities")


@dataclass(frozen=True)
class ExtractedFinancialEvent:
    """A structured event inferred from free text."""

    event_type: str
    risk_category: str
    severity: str
    amount_usd: float | None = None
    percentage: float | None = None
    market: str | None = None
    action: str | None = None
    evidence: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "risk_category": self.risk_category,
            "severity": self.severity,
            "amount_usd": self.amount_usd,
            "percentage": self.percentage,
            "market": self.market,
            "action": self.action,
            "evidence": list(self.evidence),
        }


def extract_financial_events(text: str, category_scores: dict[str, float], severity: str) -> tuple[ExtractedFinancialEvent, ...]:
    """Extract structured financial events using transparent phrase patterns and regexes."""
    normalized = _normalize(text)
    amount = _extract_amount_usd(text)
    percentage = _extract_percentage(text)
    market = _extract_market(normalized)
    events: list[ExtractedFinancialEvent] = []

    for event_type, phrases in EVENT_TYPE_PATTERNS.items():
        evidence = tuple(phrase for phrase in phrases if _contains_phrase(normalized, phrase))
        if not evidence:
            continue
        risk_category = _event_category(event_type, category_scores)
        events.append(
            ExtractedFinancialEvent(
                event_type=event_type,
                risk_category=risk_category,
                severity=severity,
                amount_usd=amount,
                percentage=percentage,
                market=market,
                action=_action_for_event(event_type),
                evidence=evidence,
            )
        )

    return tuple(events)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().replace("-", " ")).strip()


def _contains_phrase(text: str, phrase: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", text) is not None


def _extract_amount_usd(text: str) -> float | None:
    for match in _AMOUNT_RE.finditer(text):
        if not match.group("currency") and not match.group("unit"):
            continue
        number = float(match.group("number"))
        unit = (match.group("unit") or "").lower()
        if unit in {"billion", "bn"}:
            number *= 1_000_000_000
        elif unit in {"million", "mn", "m"}:
            number *= 1_000_000
        return number
    return None


def _extract_percentage(text: str) -> float | None:
    match = _PERCENT_RE.search(text)
    return float(match.group("number")) if match else None


def _extract_market(text: str) -> str | None:
    return next((market for market in _MARKETS if market in text), None)


def _event_category(event_type: str, category_scores: dict[str, float]) -> str:
    if event_type in {"fraud_loss_exposure"}:
        return "conduct_risk"
    if event_type in {"sanctions_exposure"}:
        return "sanctions_risk"
    if event_type in {"liquidity_stress"}:
        return "liquidity_risk"
    if event_type in {"systemic_risk_warning"}:
        return "systemic_risk"
    if event_type in {"restructuring", "covenant_breach", "default_warning", "downgrade"}:
        return "credit_risk"
    if event_type == "upgrade":
        return "resilience"
    return max(category_scores, key=lambda category: abs(category_scores[category]), default="credit_risk")


def _action_for_event(event_type: str) -> str | None:
    if event_type in {"downgrade", "upgrade", "restructuring"}:
        return event_type
    return None
