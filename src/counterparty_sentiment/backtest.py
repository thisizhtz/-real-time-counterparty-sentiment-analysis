"""Simple sentiment-signal backtesting utilities."""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Iterable, Mapping
from statistics import mean, pstdev
from typing import Any


def generate_signal(score: float, *, positive_threshold: float = 0.15, negative_threshold: float = -0.15) -> int:
    """Map sentiment score to long/short/flat signal."""
    if score >= positive_threshold:
        return 1
    if score <= negative_threshold:
        return -1
    return 0


def prepare_signal_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    horizon: int = 1,
    positive_threshold: float = 0.15,
    negative_threshold: float = -0.15,
) -> list[dict[str, Any]]:
    """Attach signal and strategy return fields to analyzed rows."""
    prepared: list[dict[str, Any]] = []
    return_key = f"forward_return_{horizon}d"
    for row in rows:
        returns = row.get("returns", {}) if isinstance(row.get("returns", {}), Mapping) else {}
        realized = returns.get(return_key, row.get(return_key))
        score = float(row.get("adjusted_score", row.get("score", 0.0)) or 0.0)
        signal = generate_signal(score, positive_threshold=positive_threshold, negative_threshold=negative_threshold)
        strategy_return = None if realized is None else signal * float(realized)
        updated = dict(row)
        updated["signal"] = signal
        updated["realized_return"] = realized
        updated["strategy_return"] = strategy_return
        prepared.append(updated)
    return prepared


def backtest_results(
    rows: Iterable[Mapping[str, Any]],
    *,
    horizon: int = 1,
    positive_threshold: float = 0.15,
    negative_threshold: float = -0.15,
) -> dict[str, Any]:
    """Compute compact long/short sentiment strategy metrics."""
    prepared = prepare_signal_rows(
        rows,
        horizon=horizon,
        positive_threshold=positive_threshold,
        negative_threshold=negative_threshold,
    )
    active = [row for row in prepared if row["signal"] != 0 and row["strategy_return"] is not None]
    strategy_returns = [float(row["strategy_return"]) for row in active]
    realized_returns = [float(row["realized_return"]) for row in prepared if row.get("realized_return") is not None]
    scores = [float(row.get("adjusted_score", row.get("score", 0.0)) or 0.0) for row in prepared if row.get("realized_return") is not None]

    cumulative = _compound(strategy_returns)
    hit_rate = _hit_rate(active)
    return {
        "horizon": horizon,
        "n_events": len(prepared),
        "n_trades": len(active),
        "cumulative_return": round(cumulative, 6),
        "mean_return": round(mean(strategy_returns), 6) if strategy_returns else None,
        "hit_rate": round(hit_rate, 6) if hit_rate is not None else None,
        "sharpe_ratio": _sharpe(strategy_returns),
        "max_drawdown": _max_drawdown(strategy_returns),
        "ic": _correlation(scores, realized_returns),
        "rank_ic": _correlation(_ranks(scores), _ranks(realized_returns)) if scores and realized_returns else None,
        "confusion_table": confusion_table(prepared),
    }


def confusion_table(rows: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, int]]:
    """Cross-tab sentiment label and realized return direction."""
    table: dict[str, Counter[str]] = {"positive": Counter(), "neutral": Counter(), "negative": Counter()}
    for row in rows:
        label = str(row.get("label", "neutral"))
        realized = row.get("realized_return")
        if realized is None:
            direction = "missing"
        elif float(realized) > 0:
            direction = "up"
        elif float(realized) < 0:
            direction = "down"
        else:
            direction = "flat"
        table.setdefault(label, Counter())[direction] += 1
    return {label: dict(counts) for label, counts in table.items()}


def _compound(returns: list[float]) -> float:
    value = 1.0
    for item in returns:
        value *= 1.0 + item
    return value - 1.0


def _hit_rate(rows: list[Mapping[str, Any]]) -> float | None:
    if not rows:
        return None
    wins = sum(1 for row in rows if float(row["strategy_return"]) > 0)
    return wins / len(rows)


def _sharpe(returns: list[float]) -> float | None:
    if len(returns) < 2:
        return None
    sigma = pstdev(returns)
    if sigma == 0:
        return None
    return round(mean(returns) / sigma * math.sqrt(252), 6)


def _max_drawdown(returns: list[float]) -> float | None:
    if not returns:
        return None
    equity = 1.0
    peak = 1.0
    max_drawdown = 0.0
    for item in returns:
        equity *= 1.0 + item
        peak = max(peak, equity)
        max_drawdown = min(max_drawdown, equity / peak - 1.0)
    return round(max_drawdown, 6)


def _correlation(left: list[float], right: list[float]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    left_mean = mean(left)
    right_mean = mean(right)
    numerator = sum((x - left_mean) * (y - right_mean) for x, y in zip(left, right, strict=True))
    left_var = sum((x - left_mean) ** 2 for x in left)
    right_var = sum((y - right_mean) ** 2 for y in right)
    denominator = math.sqrt(left_var * right_var)
    return None if denominator == 0 else round(numerator / denominator, 6)


def _ranks(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    index = 0
    while index < len(indexed):
        end = index
        while end + 1 < len(indexed) and indexed[end + 1][1] == indexed[index][1]:
            end += 1
        average_rank = (index + end + 2) / 2
        for original_index, _ in indexed[index : end + 1]:
            ranks[original_index] = average_rank
        index = end + 1
    return ranks
