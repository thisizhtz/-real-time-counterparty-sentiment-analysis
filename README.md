# Real-Time Counterparty Sentiment Analysis

A lightweight Python toolkit and complete static webpage for scoring streaming text about counterparties and surfacing early warning signals such as payment stress, default risk, sanctions exposure, and conduct risk.

The project is intentionally dependency-light: the baseline analyzer uses an auditable finance-oriented lexicon so teams can run it in restricted environments, understand every score, and later swap in a model-backed analyzer if needed.

## What is included

- **Event model** for normalized counterparty text observations.
- **Sentiment analyzer** with positive, negative, and risk lexicons tuned for financial counterparty monitoring.
- **Streaming state manager** with rolling per-counterparty windows.
- **JSONL CLI** for local files, pipes, or message-bus consumers that can emit newline-delimited JSON.
- **Complete static webpage** with an interactive browser-side JSONL demo.
- **Tests and examples** to validate the baseline behavior.

## Webpage demo

Open `index.html` directly in a browser, or serve the repository root locally:

```bash
python -m http.server 8000
```

Then visit `http://localhost:8000/` to use the complete interactive webpage.

## Python quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
counterparty-sentiment examples/events.jsonl --include-snapshot
```

You can also stream events through stdin:

```bash
cat examples/events.jsonl | counterparty-sentiment - --include-snapshot
```

## Input format

Each JSONL row should contain at least `counterparty` and `text`:

```json
{"counterparty":"Contoso Trading","source":"filing","timestamp":"2026-05-10T09:01:00Z","text":"Contoso disclosed a missed payment and possible restructuring."}
```

Optional fields:

- `event_id`: stable upstream event identifier.
- `source`: text source such as `news`, `filing`, `chat`, or `analyst-note`.
- `timestamp`: ISO-8601 timestamp. If omitted, the current UTC time is used.

## Output format

The CLI emits one JSON row per input event. Each row includes:

- `score`: normalized sentiment score from `-1.0` to `1.0`.
- `label`: `positive`, `neutral`, or `negative`.
- `confidence`: simple confidence proxy based on score magnitude and matched terms.
- `matched_positive_terms` / `matched_negative_terms`: lexicon terms that drove the score.
- `risk_flags`: normalized early-warning categories.
- `snapshot`: optional rolling counterparty state when `--include-snapshot` is enabled.

## Python usage

```python
from counterparty_sentiment import SentimentStream, TextEvent

stream = SentimentStream(window_size=10)
result = stream.process(
    TextEvent(
        counterparty="Northwind Capital",
        source="news",
        text="Northwind received an upgrade after reporting a stable liquidity buffer.",
    )
)

print(result.label, result.score)
print(stream.snapshot("Northwind Capital"))
```

## Development

Run the tests with:

```bash
python -m pytest
```

If `pytest` is not installed, the test suite can also be executed with the standard-library runner after installing the package in editable mode and adapting tests to `unittest`; `pytest` is recommended for day-to-day development.

## Roadmap

- Add configurable lexicon loading from YAML or JSON.
- Add connectors for Kafka, cloud queues, and market/news APIs.
- Add optional transformer-based analyzer implementations behind the same analyzer interface.
- Add dashboards for live counterparty heatmaps and alert triage.
- Add benchmark datasets and drift monitoring for production deployments.
