"""Forward return attribution for news events."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from datetime import date, datetime
from statistics import pstdev
from typing import Any

from .market_data import PriceBar, next_trading_index, normalize_price_bars
from .models import TextEvent

DEFAULT_HORIZONS = (1, 3, 5, 10)


def calculate_event_returns(
    event: TextEvent | Mapping[str, Any],
    prices: Iterable[PriceBar | Mapping[str, object] | tuple[object, object]],
    *,
    benchmark_prices: Iterable[PriceBar | Mapping[str, object] | tuple[object, object]] | None = None,
    horizons: Iterable[int] = DEFAULT_HORIZONS,
) -> dict[str, float | None]:
    """Compute forward, pre-event, abnormal, and volatility features for one event."""
    bars = normalize_price_bars(prices)
    benchmark_bars = normalize_price_bars(benchmark_prices or [])
    event_time = _event_timestamp(event)
    index = next_trading_index(bars, event_time)
    output: dict[str, float | None] = {
        "event_trading_date": None,
        "pre_event_return_1d": None,
        "volatility_20d": None,
        "abnormal_return": None,
    }
    horizons = tuple(int(horizon) for horizon in horizons)
    for horizon in horizons:
        output[f"forward_return_{horizon}d"] = None
        output[f"abnormal_return_{horizon}d"] = None

    if index is None:
        return output

    output["event_trading_date"] = bars[index].date.isoformat()  # type: ignore[assignment]
    event_close = bars[index].close
    if index > 0:
        output["pre_event_return_1d"] = _safe_return(bars[index - 1].close, event_close)
    output["volatility_20d"] = _volatility([bar.close for bar in bars[max(0, index - 20) : index + 1]])

    benchmark_index = next_trading_index(benchmark_bars, event_time) if benchmark_bars else None
    first_abnormal: float | None = None
    for horizon in horizons:
        target_index = index + horizon
        if target_index >= len(bars):
            continue
        forward = _safe_return(event_close, bars[target_index].close)
        output[f"forward_return_{horizon}d"] = forward
        abnormal = None
        if benchmark_index is not None and benchmark_index + horizon < len(benchmark_bars):
            benchmark_forward = _safe_return(benchmark_bars[benchmark_index].close, benchmark_bars[benchmark_index + horizon].close)
            abnormal = None if forward is None or benchmark_forward is None else round(forward - benchmark_forward, 6)
            output[f"abnormal_return_{horizon}d"] = abnormal
        if first_abnormal is None:
            first_abnormal = abnormal
    output["abnormal_return"] = first_abnormal
    return output


def attach_returns(
    rows: Iterable[dict[str, Any]],
    price_data: Mapping[str, Iterable[PriceBar | Mapping[str, object] | tuple[object, object]]],
    *,
    benchmark_prices: Iterable[PriceBar | Mapping[str, object] | tuple[object, object]] | None = None,
    horizons: Iterable[int] = DEFAULT_HORIZONS,
) -> list[dict[str, Any]]:
    """Attach return attribution to analyzed event rows when ticker prices exist."""
    enriched: list[dict[str, Any]] = []
    for row in rows:
        event = row.get("event", row)
        ticker = str(event.get("ticker") or row.get("ticker") or "") if isinstance(event, Mapping) else ""
        returns = calculate_event_returns(event, price_data.get(ticker, ()), benchmark_prices=benchmark_prices, horizons=horizons) if ticker else {}
        updated = dict(row)
        updated["returns"] = returns
        enriched.append(updated)
    return enriched


def _event_timestamp(event: TextEvent | Mapping[str, Any]) -> datetime | date | str:
    if isinstance(event, TextEvent):
        return event.timestamp
    return event.get("timestamp") or event.get("event_trading_date") or datetime.utcnow().date().isoformat()


def _safe_return(start: float, end: float) -> float | None:
    if start == 0 or math.isnan(start) or math.isnan(end):
        return None
    return round((end / start) - 1.0, 6)


def _volatility(closes: list[float]) -> float | None:
    returns = [_safe_return(closes[index - 1], closes[index]) for index in range(1, len(closes))]
    clean = [value for value in returns if value is not None]
    if len(clean) < 2:
        return None
    return round(pstdev(clean), 6)
