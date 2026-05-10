"""News ingestion utilities for research pipelines."""

from __future__ import annotations

import hashlib
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .entity_linking import enrich_with_entity
from .models import TextEvent


def load_news_jsonl(path: str | Path) -> list[dict[str, object]]:
    """Load local JSONL news and normalize each row to TextEvent-compatible dicts."""
    rows: list[dict[str, object]] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            rows.append(normalize_news(payload, default_source=f"jsonl:{path}", ordinal=line_number))
    return rows


def load_rss_feed(url: str, *, timeout: float = 10.0) -> list[dict[str, object]]:
    """Fetch and normalize an RSS/Atom feed URL with the Python standard library."""
    with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310 - caller-provided research URL
        content = response.read()
    root = ET.fromstring(content)
    items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
    rows: list[dict[str, object]] = []
    for index, item in enumerate(items, start=1):
        title = _child_text(item, "title")
        description = _child_text(item, "description") or _child_text(item, "summary")
        published = _child_text(item, "pubDate") or _child_text(item, "published") or _child_text(item, "updated")
        rows.append(
            normalize_news(
                {"headline": title, "text": description or title, "timestamp": _parse_datetime(published), "source": url},
                default_source="rss",
                ordinal=index,
            )
        )
    return rows


def load_yahoo_ticker_news(ticker: str, *, limit: int = 20) -> list[dict[str, object]]:
    """Load Yahoo Finance ticker news through optional yfinance when available."""
    try:
        import yfinance as yf  # type: ignore[import-not-found]
    except ImportError:
        return []

    raw_items = getattr(yf.Ticker(ticker), "news", []) or []
    rows: list[dict[str, object]] = []
    for index, item in enumerate(raw_items[:limit], start=1):
        content = item.get("content", item) if isinstance(item, dict) else {}
        title = content.get("title") or item.get("title") or ""
        summary = content.get("summary") or item.get("summary") or title
        published = content.get("pubDate") or item.get("providerPublishTime") or item.get("published")
        rows.append(
            normalize_news(
                {
                    "ticker": ticker.upper(),
                    "counterparty": ticker.upper(),
                    "headline": title,
                    "text": summary,
                    "timestamp": _parse_datetime(published),
                    "source": "yahoo_finance",
                },
                default_source="yahoo_finance",
                ordinal=index,
            )
        )
    return rows


def load_news_sources(
    sources: Iterable[str] = (),
    *,
    tickers: Iterable[str] = (),
    yahoo: bool = True,
) -> list[dict[str, object]]:
    """Load news from local JSONL paths, RSS URLs, and optionally Yahoo ticker news."""
    rows: list[dict[str, object]] = []
    for source in sources:
        if source.startswith(("http://", "https://")):
            rows.extend(load_rss_feed(source))
        else:
            rows.extend(load_news_jsonl(source))
    if yahoo:
        for ticker in tickers:
            rows.extend(load_yahoo_ticker_news(ticker))
    return rows


def normalize_news(payload: dict[str, object], *, default_source: str = "news", ordinal: int = 1) -> dict[str, object]:
    """Normalize arbitrary news payloads into TextEvent-compatible records."""
    headline = str(payload.get("headline") or payload.get("title") or "").strip()
    text = str(payload.get("text") or payload.get("summary") or payload.get("description") or headline).strip()
    timestamp = _parse_datetime(payload.get("timestamp") or payload.get("published_at") or payload.get("published"))
    source = str(payload.get("source") or default_source or "news").strip()
    counterparty = str(payload.get("counterparty") or payload.get("company") or payload.get("publisher") or headline.split(" - ")[-1] or "Unknown").strip()
    record: dict[str, object] = {
        "event_id": str(payload.get("event_id") or _event_id(source, headline, text, ordinal)),
        "timestamp": timestamp.isoformat(),
        "source": source,
        "counterparty": counterparty,
        "ticker": str(payload.get("ticker") or "").upper() or None,
        "headline": headline,
        "text": text,
    }
    return enrich_with_entity(record)


def to_text_event(payload: dict[str, object]) -> TextEvent:
    """Convert a normalized news payload to the package TextEvent model."""
    return TextEvent.from_mapping(payload)


def _event_id(source: str, headline: str, text: str, ordinal: int) -> str:
    digest = hashlib.sha1(f"{source}|{headline}|{text}|{ordinal}".encode("utf-8")).hexdigest()[:12]
    return f"news-{digest}"


def _child_text(item: ET.Element, name: str) -> str:
    direct = item.find(name)
    namespaced = item.find(f"{{http://www.w3.org/2005/Atom}}{name}")
    child = direct if direct is not None else namespaced
    return "" if child is None or child.text is None else child.text.strip()


def _parse_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, int | float):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    if isinstance(value, str) and value.strip():
        raw = value.strip()
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            try:
                from email.utils import parsedate_to_datetime

                parsed = parsedate_to_datetime(raw)
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
            except (TypeError, ValueError):
                pass
    return datetime.now(timezone.utc)
