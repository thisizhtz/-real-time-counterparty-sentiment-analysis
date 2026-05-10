#!/usr/bin/env python3
"""Fetch and normalize news records as JSONL."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from counterparty_sentiment.ingestion import load_news_sources  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch local/RSS/Yahoo news and emit normalized JSONL.")
    parser.add_argument("sources", nargs="*", help="Local JSONL files or RSS feed URLs.")
    parser.add_argument("--tickers", default="", help="Comma-separated tickers for Yahoo Finance news.")
    parser.add_argument("--no-yahoo", action="store_true", help="Skip Yahoo Finance ticker news.")
    parser.add_argument("--output", help="Optional JSONL output path. Defaults to stdout.")
    args = parser.parse_args(argv)

    tickers = [ticker.strip().upper() for ticker in args.tickers.split(",") if ticker.strip()]
    rows = load_news_sources(args.sources, tickers=tickers, yahoo=not args.no_yahoo)
    lines = [json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows]
    if args.output:
        Path(args.output).write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    else:
        for line in lines:
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
