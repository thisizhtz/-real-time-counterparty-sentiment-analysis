"""Lexicon-based NLP analyzer tuned for counterparty risk signals."""

from __future__ import annotations

import math
import re
from collections.abc import Iterable
from dataclasses import dataclass

from .models import SentimentResult, TextEvent

DEFAULT_POSITIVE_TERMS = frozenset(
    {
        "approved",
        "beat",
        "capital raise",
        "compliant",
        "confidence",
        "deleveraging",
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
        "amplify",
        "bankruptcy",
        "breach",
        "contagion",
        "default",
        "downgrade",
        "distress",
        "fraud",
        "growing links",
        "illiquid",
        "insolvent",
        "lawsuit",
        "loss",
        "missed payment",
        "negative outlook",
        "probe",
        "restructuring",
        "risk",
        "risks",
        "sanction",
        "stress",
        "systemic financial risks",
        "volatile",
        "warned",
    }
)

DEFAULT_RISK_TERMS = {
    "amplify systemic financial risks": "systemic_risk_amplification",
    "systemic financial risks": "systemic_risk",
    "systemic risk": "systemic_risk",
    "growing links": "interconnectedness_risk",
    "private credit": "private_credit_exposure",
    "banks and private credit": "bank_private_credit_linkage",
    "contagion": "contagion_risk",
    "default": "credit_default",
    "missed payment": "payment_stress",
    "sanction": "sanctions_exposure",
    "fraud": "conduct_risk",
    "bankruptcy": "bankruptcy_risk",
    "insolvent": "solvency_risk",
    "breach": "contract_breach",
}

DIMENSION_LEXICONS = {
    "credit": {
        "default": 1.0,
        "missed payment": 1.0,
        "downgrade": 0.7,
        "negative outlook": 0.6,
        "restructuring": 0.8,
        "distress": 0.7,
        "loss": 0.45,
    },
    "liquidity": {
        "illiquid": 1.0,
        "liquidity squeeze": 0.9,
        "funding pressure": 0.85,
        "withdrawal": 0.65,
        "liquidity buffer": -0.65,
    },
    "systemic": {
        "systemic financial risks": 1.0,
        "systemic risk": 1.0,
        "amplify systemic financial risks": 1.2,
        "contagion": 0.9,
        "growing links": 0.7,
        "banks and private credit": 0.85,
        "private credit": 0.45,
        "interconnected": 0.7,
        "financial stability board": 0.55,
    },
    "legal_conduct": {
        "fraud": 1.0,
        "lawsuit": 0.75,
        "probe": 0.65,
        "sanction": 0.95,
        "breach": 0.75,
    },
    "market": {
        "volatile": 0.7,
        "selloff": 0.8,
        "spread widening": 0.85,
        "drawdown": 0.65,
        "negative outlook": 0.5,
    },
    "resilience": {
        "well capitalized": -0.9,
        "investment grade": -0.75,
        "stable": -0.55,
        "upgrade": -0.7,
        "upgraded": -0.7,
        "resolved": -0.6,
        "compliant": -0.45,
    },
}

_TOKEN_PATTERN = re.compile(r"[a-z][a-z\- ]*[a-z]|[a-z]", re.IGNORECASE)
_NEGATORS = {"not", "no", "never", "without", "hardly"}
_INTENSIFIERS = {"amplify", "growing", "material", "significant", "severe", "sharp", "elevated", "warned"}


@dataclass(frozen=True)
class DimensionMatch:
    dimension: str
    term: str
    weight: float


class SentimentAnalyzer:
    """Score a text event with a deterministic, auditable finance-oriented NLP lexicon."""

    def __init__(
        self,
        positive_terms: Iterable[str] = DEFAULT_POSITIVE_TERMS,
        negative_terms: Iterable[str] = DEFAULT_NEGATIVE_TERMS,
        risk_terms: dict[str, str] | None = None,
        dimension_lexicons: dict[str, dict[str, float]] | None = None,
        positive_threshold: float = 0.15,
        negative_threshold: float = -0.15,
    ) -> None:
        self.positive_terms = tuple(sorted({term.lower() for term in positive_terms}, key=len, reverse=True))
        self.negative_terms = tuple(sorted({term.lower() for term in negative_terms}, key=len, reverse=True))
        self.risk_terms = {term.lower(): flag for term, flag in (risk_terms or DEFAULT_RISK_TERMS).items()}
        self.dimension_lexicons = {
            dimension: {term.lower(): weight for term, weight in terms.items()}
            for dimension, terms in (dimension_lexicons or DIMENSION_LEXICONS).items()
        }
        self.positive_threshold = positive_threshold
        self.negative_threshold = negative_threshold

    def analyze(self, event: TextEvent) -> SentimentResult:
        """Analyze one event and return normalized sentiment plus multi-dimensional risk scores."""
        normalized_text = _normalize(event.text)
        positive_matches = _find_terms(normalized_text, self.positive_terms)
        negative_matches = _find_terms(normalized_text, self.negative_terms)
        dimension_matches = _find_dimension_matches(normalized_text, self.dimension_lexicons)
        dimension_scores = _dimension_scores(dimension_matches)

        positive_score = sum(_term_weight(term) for term in positive_matches)
        negative_score = sum(_term_weight(term) for term in negative_matches)
        dimension_risk_pressure = sum(max(score, 0.0) for score in dimension_scores.values())
        dimension_resilience = abs(sum(min(score, 0.0) for score in dimension_scores.values()))

        negation_adjustment = _negation_adjustment(normalized_text, positive_matches, negative_matches)
        intensity = _intensity_multiplier(normalized_text)
        raw_score = (positive_score + 0.65 * dimension_resilience) - (
            negative_score + 0.75 * dimension_risk_pressure
        )
        raw_score = raw_score * intensity + negation_adjustment
        score = math.tanh(raw_score / 4.0)
        label = _label(score, self.positive_threshold, self.negative_threshold)
        confidence = min(
            1.0,
            abs(score)
            + 0.10 * (len(positive_matches) + len(negative_matches))
            + 0.08 * len(dimension_matches),
        )
        risk_flags = _risk_flags(normalized_text, self.risk_terms, dimension_scores)
        severity = _severity(dimension_scores, score)
        explanation = _explanation(positive_matches, negative_matches, dimension_scores, risk_flags)

        return SentimentResult(
            event=event,
            score=round(score, 4),
            label=label,
            confidence=round(confidence, 4),
            matched_positive_terms=tuple(positive_matches),
            matched_negative_terms=tuple(negative_matches),
            risk_flags=risk_flags,
            dimension_scores={dimension: round(value, 4) for dimension, value in dimension_scores.items()},
            severity=severity,
            explanation=explanation,
        )


def _normalize(text: str) -> str:
    return " ".join(match.group(0).lower().replace("-", " ") for match in _TOKEN_PATTERN.finditer(text))


def _find_terms(text: str, terms: Iterable[str]) -> list[str]:
    return [term for term in terms if _contains_term(text, term)]


def _find_dimension_matches(text: str, dimension_lexicons: dict[str, dict[str, float]]) -> list[DimensionMatch]:
    matches: list[DimensionMatch] = []
    for dimension, lexicon in dimension_lexicons.items():
        for term, weight in sorted(lexicon.items(), key=lambda item: len(item[0]), reverse=True):
            if _contains_term(text, term):
                matches.append(DimensionMatch(dimension=dimension, term=term, weight=weight))
    return matches


def _dimension_scores(matches: list[DimensionMatch]) -> dict[str, float]:
    scores = {dimension: 0.0 for dimension in DIMENSION_LEXICONS}
    for match in matches:
        scores.setdefault(match.dimension, 0.0)
        scores[match.dimension] += match.weight
    return {dimension: math.tanh(score / 2.0) for dimension, score in scores.items()}


def _contains_term(text: str, term: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text) is not None


def _term_weight(term: str) -> float:
    return 1.0 + 0.25 * (len(term.split()) - 1)


def _intensity_multiplier(text: str) -> float:
    matched_intensifiers = sum(1 for term in _INTENSIFIERS if _contains_term(text, term))
    return min(1.4, 1.0 + 0.08 * matched_intensifiers)


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


def _risk_flags(text: str, risk_terms: dict[str, str], dimension_scores: dict[str, float]) -> tuple[str, ...]:
    flags = {flag for term, flag in risk_terms.items() if _contains_term(text, term)}
    flags.update(f"{dimension}_risk" for dimension, score in dimension_scores.items() if score >= 0.45)
    return tuple(sorted(flags))


def _severity(dimension_scores: dict[str, float], score: float) -> str:
    max_dimension = max((value for value in dimension_scores.values()), default=0.0)
    if score <= -0.65 or max_dimension >= 0.75:
        return "high"
    if score <= -0.35 or max_dimension >= 0.45:
        return "medium"
    return "low"


def _explanation(
    positive_matches: list[str],
    negative_matches: list[str],
    dimension_scores: dict[str, float],
    risk_flags: tuple[str, ...],
) -> str:
    top_dimensions = [
        f"{dimension}={score:.2f}"
        for dimension, score in sorted(dimension_scores.items(), key=lambda item: abs(item[1]), reverse=True)[:3]
        if abs(score) > 0.05
    ]
    parts = []
    if negative_matches:
        parts.append(f"negative terms: {', '.join(negative_matches[:4])}")
    if positive_matches:
        parts.append(f"positive terms: {', '.join(positive_matches[:4])}")
    if top_dimensions:
        parts.append(f"dimensions: {', '.join(top_dimensions)}")
    if risk_flags:
        parts.append(f"flags: {', '.join(risk_flags[:4])}")
    return "; ".join(parts) or "no material lexicon signal detected"


def _label(score: float, positive_threshold: float, negative_threshold: float) -> str:
    if score >= positive_threshold:
        return "positive"
    if score <= negative_threshold:
        return "negative"
    return "neutral"
