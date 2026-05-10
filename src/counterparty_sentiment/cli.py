"""Command-line interface for JSONL sentiment streams."""

from __future__ import annotations

import argparse
import json
import sys
from typing import TextIO

from .models import TextEvent
from .streaming import SentimentStream


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze JSONL counterparty events with explainable financial risk NLP.")
    parser.add_argument(
        "input",
        nargs="?",
        help="Path to a JSONL file. Reads from stdin when omitted or set to '-'.",
    )
    parser.add_argument(
        "--window-size",
        type=int,
        default=25,
        help="Rolling window size per counterparty.",
    )
    parser.add_argument(
        "--include-snapshot",
        action="store_true",
        help="Include rolling counterparty snapshot in each output row.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    stream = SentimentStream(window_size=args.window_size)

    try:
        input_stream = _open_input(args.input)
        with input_stream:
            for line_number, line in enumerate(input_stream, start=1):
                if not line.strip():
                    continue
                payload = json.loads(line)
                event = TextEvent.from_mapping(payload)
                result = stream.process(event)
                output = result.to_dict()
                if args.include_snapshot:
                    snapshot = stream.snapshot(event.counterparty)
                    output["snapshot"] = snapshot.to_dict() if snapshot else None
                print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"counterparty-sentiment: invalid input at line {locals().get('line_number', 1)}: {exc}", file=sys.stderr)
        return 2

    return 0


def _open_input(path: str | None) -> TextIO:
    if path in (None, "-"):
        return sys.stdin
    return open(path, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
