"""Command-line interface for JSONL sentiment streams and news-to-return research."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import timedelta
from pathlib import Path
from typing import Any, TextIO

from .analyzer import SentimentAnalyzer
from .backtest import backtest_results
from .ingestion import load_news_sources
from .market_data import fetch_ohlcv
from .ml import OptionalFinBERTScorer
from .models import TextEvent
from .returns import DEFAULT_HORIZONS, attach_returns
from .streaming import SentimentStream


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze financial news with explainable NLP and optional return attribution.")
    parser.add_argument(
        "input",
        nargs="?",
        help="Path to a JSONL file, RSS URL when --fetch-news is used, or '-' / omitted for stdin.",
    )
    parser.add_argument("--window-size", type=int, default=25, help="Rolling window size per counterparty.")
    parser.add_argument("--include-snapshot", action="store_true", help="Include rolling counterparty snapshot in each output row.")
    parser.add_argument("--fetch-news", action="store_true", help="Normalize news from local JSONL, RSS URLs, and Yahoo ticker news.")
    parser.add_argument("--tickers", default="", help="Comma-separated tickers for Yahoo Finance news or return attribution.")
    parser.add_argument("--model", choices=("lexicon", "finbert", "hybrid"), default="lexicon", help="Sentiment model mode.")
    parser.add_argument("--with-returns", action="store_true", help="Attach forward returns using optional yfinance market data.")
    parser.add_argument("--benchmark", default="SPY", help="Benchmark ticker for abnormal returns.")
    parser.add_argument("--horizons", default="1,3,5,10", help="Comma-separated forward return horizons in trading days.")
    parser.add_argument("--output", help="Write event-level JSONL results to this path instead of stdout.")
    parser.add_argument("--backtest", action="store_true", help="Emit a final backtest summary row.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    horizons = _parse_horizons(args.horizons)

    try:
        analyzer = _build_analyzer(args.model)
        stream = SentimentStream(window_size=args.window_size, analyzer=analyzer)
        events = _load_events(args)
        rows = _analyze_events(events, stream, include_snapshot=args.include_snapshot)
        if args.with_returns:
            rows = _attach_market_returns(rows, args, horizons)
        summary = backtest_results(rows, horizon=horizons[0]) if args.backtest else None
        _write_outputs(rows, summary, args.output)
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"counterparty-sentiment: invalid input: {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"counterparty-sentiment: {exc}", file=sys.stderr)
        return 3

    return 0


def _build_analyzer(model: str) -> SentimentAnalyzer:
    if model == "lexicon":
        return SentimentAnalyzer()
    scorer = OptionalFinBERTScorer()
    return SentimentAnalyzer(ml_model=scorer, ml_weight=1.0 if model == "finbert" else 0.5)


def _load_events(args: argparse.Namespace) -> list[TextEvent]:
    tickers = _parse_tickers(args.tickers)
    if args.fetch_news:
        sources = [] if args.input in (None, "-") else [args.input]
        return [TextEvent.from_mapping(row) for row in load_news_sources(sources, tickers=tickers, yahoo=bool(tickers))]

    input_stream = _open_input(args.input)
    events: list[TextEvent] = []
    with input_stream:
        for line_number, line in enumerate(input_stream, start=1):
            if not line.strip():
                continue
            try:
                events.append(TextEvent.from_mapping(json.loads(line)))
            except (KeyError, ValueError, json.JSONDecodeError) as exc:
                raise ValueError(f"line {line_number}: {exc}") from exc
    return events


def _analyze_events(events: list[TextEvent], stream: SentimentStream, *, include_snapshot: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event in events:
        result = stream.process(event)
        output = result.to_dict()
        if include_snapshot:
            snapshot = stream.snapshot(event.counterparty)
            output["snapshot"] = snapshot.to_dict() if snapshot else None
        rows.append(output)
    return rows


def _attach_market_returns(rows: list[dict[str, Any]], args: argparse.Namespace, horizons: tuple[int, ...]) -> list[dict[str, Any]]:
    tickers = sorted({str(row["event"].get("ticker") or "").upper() for row in rows if row.get("event", {}).get("ticker")})
    tickers.extend(ticker for ticker in _parse_tickers(args.tickers) if ticker not in tickers)
    if not tickers:
        return attach_returns(rows, {}, horizons=horizons)

    timestamps = [TextEvent.from_mapping(row["event"]).timestamp for row in rows]
    start = min(timestamps) - timedelta(days=45)
    end = max(timestamps) + timedelta(days=max(DEFAULT_HORIZONS) * 4)
    price_data: dict[str, object] = {}
    benchmark_prices = None
    for ticker in tickers:
        try:
            price_data[ticker] = fetch_ohlcv(ticker, start, end)
        except RuntimeError:
            price_data[ticker] = []
    try:
        benchmark_prices = fetch_ohlcv(args.benchmark, start, end)
    except RuntimeError:
        benchmark_prices = None
    return attach_returns(rows, price_data, benchmark_prices=benchmark_prices, horizons=horizons)


def _write_outputs(rows: list[dict[str, Any]], summary: dict[str, Any] | None, output_path: str | None) -> None:
    lines = [json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows]
    if summary is not None:
        lines.append(json.dumps({"backtest": summary}, ensure_ascii=False, sort_keys=True))
    if output_path:
        Path(output_path).write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    else:
        for line in lines:
            print(line)


def _parse_tickers(value: str) -> list[str]:
    return [ticker.strip().upper() for ticker in value.split(",") if ticker.strip()]


def _parse_horizons(value: str) -> tuple[int, ...]:
    horizons = tuple(int(item.strip()) for item in value.split(",") if item.strip())
    return horizons or DEFAULT_HORIZONS


def _open_input(path: str | None) -> TextIO:
    if path in (None, "-"):
        return sys.stdin
    return open(path, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
