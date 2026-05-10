"""Lightweight company-name-to-ticker entity linking.

This module deliberately avoids heavyweight NER dependencies.  It starts with a
small auditable alias dictionary and simple string matching so the research
pipeline can attach tickers to news before future NER or knowledge-graph
integration.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Mapping


@dataclass(frozen=True)
class EntityLink:
    """Ticker mapping result for one company mention."""

    ticker: str | None
    canonical_name: str | None
    confidence: float
    matched_alias: str | None = None

    def to_dict(self) -> dict[str, str | float | None]:
        return {
            "ticker": self.ticker,
            "canonical_name": self.canonical_name,
            "confidence": self.confidence,
            "matched_alias": self.matched_alias,
        }


DEFAULT_COMPANY_TICKERS: dict[str, dict[str, object]] = {
    "JPM": {"canonical_name": "JPMorgan Chase", "aliases": ("jpmorgan", "jp morgan", "jpmorgan chase", "chase bank")},
    "BAC": {"canonical_name": "Bank of America", "aliases": ("bank of america", "bofa", "boa")},
    "C": {"canonical_name": "Citigroup", "aliases": ("citigroup", "citi", "citibank")},
    "GS": {"canonical_name": "Goldman Sachs", "aliases": ("goldman", "goldman sachs")},
    "MS": {"canonical_name": "Morgan Stanley", "aliases": ("morgan stanley",)},
    "WFC": {"canonical_name": "Wells Fargo", "aliases": ("wells fargo",)},
    "HSBC": {"canonical_name": "HSBC", "aliases": ("hsbc", "hongkong and shanghai banking")},
    "BLK": {"canonical_name": "BlackRock", "aliases": ("blackrock",)},
    "BX": {"canonical_name": "Blackstone", "aliases": ("blackstone",)},
    "LMT": {"canonical_name": "Lockheed Martin", "aliases": ("lockheed", "lockheed martin")},
    "NOC": {"canonical_name": "Northrop Grumman", "aliases": ("northrop", "northrop grumman")},
    "RTX": {"canonical_name": "RTX", "aliases": ("rtx", "raytheon", "raytheon technologies")},
    "BA": {"canonical_name": "Boeing", "aliases": ("boeing",)},
    "GD": {"canonical_name": "General Dynamics", "aliases": ("general dynamics",)},
    "TSLA": {"canonical_name": "Tesla", "aliases": ("tesla",)},
    "NVDA": {"canonical_name": "NVIDIA", "aliases": ("nvidia", "nvda")},
    "AAPL": {"canonical_name": "Apple", "aliases": ("apple",)},
    "MSFT": {"canonical_name": "Microsoft", "aliases": ("microsoft",)},
    "GOOGL": {"canonical_name": "Alphabet", "aliases": ("alphabet", "google")},
    "META": {"canonical_name": "Meta Platforms", "aliases": ("meta", "facebook")},
    "AMZN": {"canonical_name": "Amazon", "aliases": ("amazon",)},
    "XOM": {"canonical_name": "Exxon Mobil", "aliases": ("exxon", "exxon mobil", "exxonmobil")},
}


def link_company(
    text: str,
    mapping: Mapping[str, Mapping[str, object]] | None = None,
    *,
    min_confidence: float = 0.72,
) -> EntityLink:
    """Return the best ticker link for a text snippet or company name."""
    normalized = _normalize(text)
    candidates = mapping or DEFAULT_COMPANY_TICKERS
    best = EntityLink(None, None, 0.0, None)

    for ticker, metadata in candidates.items():
        canonical_name = str(metadata.get("canonical_name", ticker))
        aliases = tuple(str(alias) for alias in metadata.get("aliases", (canonical_name,)))
        for alias in (ticker, canonical_name, *aliases):
            confidence = _match_confidence(normalized, _normalize(alias), ticker)
            if confidence > best.confidence:
                best = EntityLink(ticker=ticker, canonical_name=canonical_name, confidence=round(confidence, 4), matched_alias=alias)

    return best if best.confidence >= min_confidence else EntityLink(None, None, round(best.confidence, 4), best.matched_alias)


def enrich_with_entity(payload: dict[str, object], mapping: Mapping[str, Mapping[str, object]] | None = None) -> dict[str, object]:
    """Attach ticker and canonical counterparty fields to a normalized news row."""
    search_text = " ".join(str(payload.get(key, "")) for key in ("counterparty", "headline", "text"))
    link = link_company(search_text, mapping)
    enriched = dict(payload)
    if link.ticker:
        enriched.setdefault("ticker", link.ticker)
        enriched["ticker"] = enriched.get("ticker") or link.ticker
        enriched["counterparty"] = link.canonical_name or enriched.get("counterparty") or link.ticker
    enriched["entity_link"] = link.to_dict()
    return enriched


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-zA-Z0-9\s]", " ", value.lower())).strip()


def _match_confidence(text: str, alias: str, ticker: str) -> float:
    if not alias:
        return 0.0
    ticker_pattern = rf"(?<![a-z0-9]){re.escape(ticker.lower())}(?![a-z0-9])"
    if re.search(ticker_pattern, text):
        return 0.98
    alias_pattern = rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])"
    if re.search(alias_pattern, text):
        return 0.95 if len(alias) > 3 else 0.9
    window_scores = [SequenceMatcher(None, alias, token).ratio() for token in _candidate_windows(text, len(alias.split()))]
    return max(window_scores, default=0.0) * 0.82


def _candidate_windows(text: str, width: int) -> list[str]:
    words = text.split()
    if not words:
        return []
    width = max(1, width)
    return [" ".join(words[index : index + width]) for index in range(0, max(1, len(words) - width + 1))]
