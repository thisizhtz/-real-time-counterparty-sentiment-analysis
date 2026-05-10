"""Lexicon-based sentiment analyzer tuned for counterparty risk signals."""

from __future__ import annotations

import math
import re
from collections.abc import Iterable

from .models import SentimentResult, TextEvent

DEFAULT_POSITIVE_TERMS = frozenset(
    {
        "approved",
        "beat",
        "compliant",
        "confidence",
        "improved",
        "investment grade",
        "liquidity buffer",
        "profitable",
        "recovered",
        "resolved",
        "stable",
        "upgrade",
        "upgraded",
        "well capitalized",
    }
)

DEFAULT_NEGATIVE_TERMS = frozenset(
    {
        "bankruptcy",
        "breach",
        "default",
        "downgrade",
        "fraud",
        "illiquid",
        "insolvent",
        "lawsuit",
        "loss",
        "missed payment",
        "negative outlook",
        "probe",
        "restructuring",
        "sanction",
        "volatile",
    }
)

DEFAULT_RISK_TERMS = {
    "default": "credit_default",
    "missed payment": "payment_stress",
    "sanction": "sanctions_exposure",
    "fraud": "conduct_risk",
    "bankruptcy": "bankruptcy_risk",
    "insolvent": "solvency_risk",
    "breach": "contract_breach",
}

_TOKEN_PATTERN = re.compile(r"[a-z][a-z\- ]*[a-z]|[a-z]", re.IGNORECASE)
_NEGATORS = {"not", "no", "never", "without", "hardly"}


class SentimentAnalyzer:
    """Score a text event with a simple, auditable finance-oriented lexicon."""

    def __init__(
        self,
        positive_terms: Iterable[str] = DEFAULT_POSITIVE_TERMS,
        negative_terms: Iterable[str] = DEFAULT_NEGATIVE_TERMS,
        risk_terms: dict[str, str] | None = None,
        positive_threshold: float = 0.15,
        negative_threshold: float = -0.15,
    ) -> None:
        self.positive_terms = tuple(sorted({term.lower() for term in positive_terms}, key=len, reverse=True))
        self.negative_terms = tuple(sorted({term.lower() for term in negative_terms}, key=len, reverse=True))
        self.risk_terms = {term.lower(): flag for term, flag in (risk_terms or DEFAULT_RISK_TERMS).items()}
        self.positive_threshold = positive_threshold
        self.negative_threshold = negative_threshold

    def analyze(self, event: TextEvent) -> SentimentResult:
        """Analyze one event and return a normalized sentiment result."""
        normalized_text = _normalize(event.text)
        positive_matches = _find_terms(normalized_text, self.positive_terms)
        negative_matches = _find_terms(normalized_text, self.negative_terms)

        positive_score = sum(_term_weight(term) for term in positive_matches)
        negative_score = sum(_term_weight(term) for term in negative_matches)

        negation_adjustment = _negation_adjustment(normalized_text, positive_matches, negative_matches)
        raw_score = positive_score - negative_score + negation_adjustment
        score = math.tanh(raw_score / 3.0)
        label = _label(score, self.positive_threshold, self.negative_threshold)
        confidence = min(1.0, abs(score) + 0.15 * (len(positive_matches) + len(negative_matches)))
        risk_flags = tuple(
            flag for term, flag in self.risk_terms.items() if _contains_term(normalized_text, term)
        )

        return SentimentResult(
            event=event,
            score=round(score, 4),
            label=label,
            confidence=round(confidence, 4),
            matched_positive_terms=tuple(positive_matches),
            matched_negative_terms=tuple(negative_matches),
            risk_flags=risk_flags,
        )


def _normalize(text: str) -> str:
    return " ".join(match.group(0).lower().replace("-", " ") for match in _TOKEN_PATTERN.finditer(text))


def _find_terms(text: str, terms: Iterable[str]) -> list[str]:
    return [term for term in terms if _contains_term(text, term)]


def _contains_term(text: str, term: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text) is not None


def _term_weight(term: str) -> float:
    return 1.0 + 0.25 * (len(term.split()) - 1)


def _negation_adjustment(text: str, positive_matches: list[str], negative_matches: list[str]) -> float:
    words = text.split()
    adjustment = 0.0
    for index, word in enumerate(words):
        if word not in _NEGATORS:
            continue
        window = " ".join(words[index + 1 : index + 4])
        if any(term in window for term in positive_matches):
            adjustment -= 1.0
        if any(term in window for term in negative_matches):
            adjustment += 1.0
    return adjustment


def _label(score: float, positive_threshold: float, negative_threshold: float) -> str:
    if score >= positive_threshold:
        return "positive"
    if score <= negative_threshold:
        return "negative"
    return "neutral"
