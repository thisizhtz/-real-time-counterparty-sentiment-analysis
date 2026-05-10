"""Explainable financial NLP analyzer for counterparty risk monitoring."""

from __future__ import annotations

import math
import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone

from .extraction import extract_financial_events
from .lexicons import (
    INTENSIFIERS,
    NEGATIVE_TERMS,
    NEGATORS,
    POSITIVE_TERMS,
    RISK_LEXICON,
    SOURCE_RELIABILITY,
    SUPPRESSION_PATTERNS,
    CATEGORY_ALIASES,
    TERM_RISK_FLAGS,
    UNCERTAINTY_TERMS,
)
from .ml import MLSentimentModel
from .models import SentimentResult, TextEvent

DEFAULT_POSITIVE_TERMS = POSITIVE_TERMS
DEFAULT_NEGATIVE_TERMS = NEGATIVE_TERMS
DIMENSION_LEXICONS = RISK_LEXICON
DEFAULT_RISK_TERMS = TERM_RISK_FLAGS

_TOKEN_PATTERN = re.compile(r"[a-z][a-z\- ]*[a-z]|[a-z]|\d+(?:\.\d+)?%?", re.IGNORECASE)


@dataclass(frozen=True)
class TermMatch:
    """A weighted lexicon match with context-aware adjustment."""

    category: str
    term: str
    base_weight: float
    adjusted_weight: float
    context: str
    suppressed: bool = False


class SentimentAnalyzer:
    """Score text with auditable weighted financial risk lexicons and optional ML blending."""

    def __init__(
        self,
        positive_terms: Iterable[str] = DEFAULT_POSITIVE_TERMS,
        negative_terms: Iterable[str] = DEFAULT_NEGATIVE_TERMS,
        risk_terms: dict[str, str] | None = None,
        dimension_lexicons: dict[str, dict[str, float]] | None = None,
        positive_threshold: float = 0.15,
        negative_threshold: float = -0.15,
        ml_model: MLSentimentModel | None = None,
        ml_weight: float = 0.0,
    ) -> None:
        self.positive_terms = tuple(sorted({term.lower() for term in positive_terms}, key=len, reverse=True))
        self.negative_terms = tuple(sorted({term.lower() for term in negative_terms}, key=len, reverse=True))
        self.risk_terms = {term.lower(): flag for term, flag in (risk_terms or DEFAULT_RISK_TERMS).items()}
        self.dimension_lexicons = {
            dimension: {term.lower(): weight for term, weight in terms.items()}
            for dimension, terms in (dimension_lexicons or RISK_LEXICON).items()
        }
        self.positive_threshold = positive_threshold
        self.negative_threshold = negative_threshold
        self.ml_model = ml_model
        self.ml_weight = max(0.0, min(1.0, ml_weight))

    def analyze(self, event: TextEvent) -> SentimentResult:
        """Analyze one event and return normalized risk, event extraction, and audit evidence."""
        normalized_text = _normalize(event.text)
        term_matches = _find_weighted_matches(normalized_text, self.dimension_lexicons)
        category_scores = _category_scores(term_matches)
        dimension_scores = {CATEGORY_ALIASES.get(category, category): round(math.tanh(score / 1.5), 4) for category, score in category_scores.items()}

        matched_positive_terms = tuple(match.term for match in term_matches if match.adjusted_weight < 0 and not match.suppressed)
        matched_negative_terms = tuple(match.term for match in term_matches if match.adjusted_weight > 0 and not match.suppressed)
        raw_pressure = sum(score for category, score in category_scores.items() if category != "resilience" and score > 0)
        resilience = abs(category_scores.get("resilience", 0.0))
        intensity = _intensity_multiplier(normalized_text)
        uncertainty = _uncertainty_discount(normalized_text)
        source_reliability = _source_reliability(event.source)
        recency_weight = _recency_weight(event.timestamp)

        rule_score = math.tanh(((resilience * 0.85) - raw_pressure) * intensity * uncertainty / 3.0)
        ml_score = None
        if self.ml_model is not None and self.ml_weight > 0:
            prediction = self.ml_model.predict(event.text)
            ml_score = prediction.score
            rule_score = (1 - self.ml_weight) * rule_score + self.ml_weight * ml_score

        adjusted_score = rule_score * (0.55 + 0.45 * source_reliability) * recency_weight
        label = _label(adjusted_score, self.positive_threshold, self.negative_threshold)
        severity_score = _severity_score(category_scores, source_reliability, recency_weight)
        severity = _severity_label(severity_score)
        risk_flags = _risk_flags(category_scores, normalized_text, self.risk_terms)
        extracted_events = extract_financial_events(event.text, category_scores, severity)
        confidence = _confidence(term_matches, source_reliability, uncertainty, extracted_events)
        explanation = _explanation(term_matches, dimension_scores, risk_flags, source_reliability, recency_weight)

        return SentimentResult(
            event=event,
            score=round(rule_score, 4),
            label=label,
            confidence=round(confidence, 4),
            matched_positive_terms=matched_positive_terms,
            matched_negative_terms=matched_negative_terms,
            risk_flags=risk_flags,
            dimension_scores=dimension_scores,
            severity=severity,
            explanation=explanation,
            extracted_events=extracted_events,
            category_scores={category: round(score, 4) for category, score in category_scores.items()},
            source_reliability=round(source_reliability, 4),
            recency_weight=round(recency_weight, 4),
            adjusted_score=round(adjusted_score, 4),
            ml_score=round(ml_score, 4) if ml_score is not None else None,
        )


def _normalize(text: str) -> str:
    return " ".join(match.group(0).lower().replace("-", " ") for match in _TOKEN_PATTERN.finditer(text))


def _find_weighted_matches(text: str, lexicon: dict[str, dict[str, float]]) -> list[TermMatch]:
    matches: list[TermMatch] = []
    words = text.split()
    for category, terms in lexicon.items():
        category_suppressed = _category_suppressed(text, category)
        for term, weight in sorted(terms.items(), key=lambda item: len(item[0]), reverse=True):
            for match in re.finditer(rf"(?<!\w){re.escape(term)}(?!\w)", text):
                context = _context_window(words, match.start(), text)
                adjusted_weight = _contextual_weight(weight, context, category_suppressed)
                matches.append(
                    TermMatch(
                        category=category,
                        term=term,
                        base_weight=weight,
                        adjusted_weight=adjusted_weight,
                        context=context,
                        suppressed=category_suppressed or abs(adjusted_weight) < abs(weight) * 0.35,
                    )
                )
                break
    return matches


def _category_suppressed(text: str, category: str) -> bool:
    return any(pattern in text for pattern in SUPPRESSION_PATTERNS.get(category, ()))


def _context_window(words: list[str], char_position: int, text: str, radius: int = 5) -> str:
    prefix = text[:char_position]
    index = len(prefix.split())
    start = max(0, index - radius)
    end = min(len(words), index + radius + 1)
    return " ".join(words[start:end])


def _contextual_weight(weight: float, context: str, category_suppressed: bool) -> float:
    adjusted = weight
    suppression = category_suppressed or any(negator in context.split() for negator in NEGATORS)
    dismissal = "dismissed" in context or "no evidence" in context
    if suppression and weight > 0:
        adjusted = -abs(weight) * 0.55
    elif suppression:
        adjusted *= 0.5
    if dismissal and weight > 0:
        adjusted = min(adjusted, -abs(weight) * 0.45)
    elif dismissal:
        adjusted *= 1.2
    if any(term in context for term in INTENSIFIERS) and adjusted > 0:
        adjusted *= 1.18
    if any(term in context for term in UNCERTAINTY_TERMS) and adjusted > 0:
        adjusted *= 0.72
    return adjusted


def _category_scores(matches: list[TermMatch]) -> dict[str, float]:
    scores = {category: 0.0 for category in RISK_LEXICON}
    for match in matches:
        scores.setdefault(match.category, 0.0)
        scores[match.category] += match.adjusted_weight
    return scores


def _intensity_multiplier(text: str) -> float:
    matched_intensifiers = sum(1 for term in INTENSIFIERS if _contains_term(text, term))
    return min(1.45, 1.0 + 0.08 * matched_intensifiers)


def _uncertainty_discount(text: str) -> float:
    uncertainty_count = sum(1 for term in UNCERTAINTY_TERMS if _contains_term(text, term))
    return max(0.68, 1.0 - 0.08 * uncertainty_count)


def _source_reliability(source: str) -> float:
    normalized = source.strip().lower()
    return SOURCE_RELIABILITY.get(normalized, SOURCE_RELIABILITY.get(normalized.replace("_", " "), 0.65))


def _recency_weight(timestamp: datetime) -> float:
    event_time = timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)
    age_hours = max(0.0, (datetime.now(timezone.utc) - event_time.astimezone(timezone.utc)).total_seconds() / 3600)
    return max(0.35, math.exp(-age_hours / (24 * 14)))


def _severity_score(category_scores: dict[str, float], source_reliability: float, recency_weight: float) -> float:
    max_risk = max((score for category, score in category_scores.items() if category != "resilience"), default=0.0)
    aggregate = sum(max(score, 0.0) for category, score in category_scores.items() if category != "resilience")
    return min(1.0, (0.55 * math.tanh(max_risk) + 0.45 * math.tanh(aggregate / 2.5)) * source_reliability * recency_weight)


def _severity_label(severity_score: float) -> str:
    if severity_score >= 0.62:
        return "high"
    if severity_score >= 0.32:
        return "medium"
    return "low"


def _confidence(
    matches: list[TermMatch],
    source_reliability: float,
    uncertainty: float,
    extracted_events: tuple[object, ...],
) -> float:
    effective_matches = [match for match in matches if not match.suppressed]
    evidence_strength = min(1.0, 0.12 * len(effective_matches) + 0.12 * len(extracted_events))
    suppression_penalty = 0.04 * sum(1 for match in matches if match.suppressed)
    return max(0.05, min(1.0, 0.28 + evidence_strength + 0.32 * source_reliability + 0.20 * uncertainty - suppression_penalty))


def _risk_flags(category_scores: dict[str, float], text: str, risk_terms: dict[str, str]) -> tuple[str, ...]:
    flags = {category for category, score in category_scores.items() if category != "resilience" and score >= 0.45}
    flags.update(flag for term, flag in risk_terms.items() if _contains_term(text, term))
    return tuple(sorted(flags))


def _explanation(
    matches: list[TermMatch],
    dimension_scores: dict[str, float],
    risk_flags: tuple[str, ...],
    source_reliability: float,
    recency_weight: float,
) -> str:
    active_matches = [match for match in matches if not match.suppressed]
    suppressed = [match for match in matches if match.suppressed]
    top_terms = sorted(active_matches, key=lambda match: abs(match.adjusted_weight), reverse=True)[:5]
    top_dimensions = [
        f"{dimension}={score:.2f}"
        for dimension, score in sorted(dimension_scores.items(), key=lambda item: abs(item[1]), reverse=True)[:4]
        if abs(score) > 0.05
    ]
    parts = []
    if top_terms:
        parts.append("terms: " + ", ".join(f"{match.term}({match.category}:{match.adjusted_weight:.2f})" for match in top_terms))
    if top_dimensions:
        parts.append("dimensions: " + ", ".join(top_dimensions))
    if risk_flags:
        parts.append("flags: " + ", ".join(risk_flags[:5]))
    if suppressed:
        parts.append("suppressed: " + ", ".join(match.term for match in suppressed[:3]))
    parts.append(f"source={source_reliability:.2f}")
    parts.append(f"recency={recency_weight:.2f}")
    return "; ".join(parts) if parts else "no material lexicon signal detected"


def _contains_term(text: str, term: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text) is not None


def _label(score: float, positive_threshold: float, negative_threshold: float) -> str:
    if score >= positive_threshold:
        return "positive"
    if score <= negative_threshold:
        return "negative"
    return "neutral"
