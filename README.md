# Real-Time Counterparty Sentiment Analysis

A complete static webpage and lightweight Python toolkit for turning streaming counterparty text into explainable sentiment scores, multi-dimensional risk scores, early-warning risk flags, rolling monitoring snapshots, live-news style sentiment views, and research-oriented stock-pick queues.

The repository is designed to be useful in two modes:

1. **Webpage-first demo**: open a polished Chinese horizontal dashboard with natural-language input, FinTransformer-style scoring, a simulated live-news sentiment radar, and a stock-pick page that runs fully in the browser.
2. **Python toolkit**: install the package locally and process JSONL events through the CLI or the `counterparty_sentiment` Python API.

The baseline analyzer is intentionally dependency-light and auditable. It uses finance-oriented lexicons, deterministic scoring, intensity/negation handling, multi-dimensional risk scoring, and transparent matched-term output so risk teams can understand every score before replacing or augmenting it with a model-backed analyzer.

## What is included

- **Complete static webpage** with a clean bright horizontal UI, FinTransformer model positioning, natural-language analysis, simulated live-news sentiment radar, stock-pick queue, deployment guidance, responsive styling, and browser-side analysis.
- **Event model** for normalized counterparty text observations.
- **Institutional-style risk engine** with weighted financial risk lexicons, context suppression, source reliability, recency weighting, event extraction, optional ML hooks, and category scores for credit, conduct, liquidity, systemic, sanctions, market, and resilience signals.
- **Streaming state manager** with bounded rolling per-counterparty windows.
- **JSONL CLI** for local files, pipes, or message-bus consumers that can emit newline-delimited JSON.
- **Tests, examples, and CI** to validate analyzer behavior, CLI output, static assets, and frontend analysis logic.

## Webpage demo

Open `index.html` directly in a browser, or serve the repository root locally:

```bash
python -m http.server 8000
```

Then visit `http://localhost:8000/` to use the full interactive webpage.

The webpage lets you:

- switch horizontally between overview, smart recognition, live news, stock picks, and deployment pages;
- paste natural-language Chinese or English news, filings, notes, chats, or legacy newline-delimited JSON events;
- restore a built-in natural-language sample event stream;
- analyze events locally in the browser without uploading text;
- view event-level labels, scores, confidence values, severity, matched terms, explanations, model names, and risk flags;
- view summary metrics, rolling trend chart, top counterparties by risk, category breakdown, event timeline, simulated live-news sentiment radar, and stock-pick candidates.


## Financial news-to-return research pipeline

The project now supports an end-to-end quant research prototype:

```text
Financial News NLP
  ├─ Ingest local JSONL, RSS feeds, or optional Yahoo Finance ticker news
  ├─ Link company names to tickers with an auditable alias dictionary
  ├─ Normalize records into TextEvent rows
  ↓
Risk Event Extraction
  ├─ Explainable lexicon / optional FinBERT / hybrid sentiment scoring
  ├─ Structured event extraction: downgrade, covenant breach, liquidity stress, sanctions, fraud, upgrade
  └─ Rolling counterparty snapshots for monitoring
  ↓
Sentiment Signal
  ├─ positive score above threshold → long
  ├─ negative score below threshold → short
  └─ otherwise flat
  ↓
Return Attribution
  ├─ Optional yfinance OHLCV download
  ├─ Next-trading-day alignment for weekend and holiday news
  ├─ Forward returns: 1d, 3d, 5d, 10d
  ├─ Pre-event return and 20-day volatility
  └─ Abnormal return versus SPY or another benchmark
  ↓
Backtest
  ├─ Cumulative return, mean return, hit rate, Sharpe ratio, max drawdown
  ├─ IC and Rank IC
  └─ Confusion table between sentiment label and realized return direction
```

### News ingestion

Normalize news from a local JSONL file:

```bash
scripts/fetch_news.py examples/events.jsonl --no-yahoo --output normalized_news.jsonl
```

Fetch RSS plus optional Yahoo ticker news when `yfinance` is installed:

```bash
scripts/fetch_news.py "https://example.com/feed.xml" --tickers JPM,LMT,NVDA --output news.jsonl
```

Each normalized row is compatible with `TextEvent` and includes `event_id`, `timestamp`, `source`, `counterparty`, `ticker`, `headline`, and `text` when available.

### CLI research examples

Preserve the existing lexicon-only JSONL workflow:

```bash
counterparty-sentiment examples/events.jsonl --include-snapshot
```

Run the research pipeline on normalized or fetched news:

```bash
counterparty-sentiment news.jsonl --fetch-news --model lexicon --backtest --output results.jsonl
```

Use FinBERT or hybrid mode if `transformers` is installed:

```bash
counterparty-sentiment news.jsonl --fetch-news --model hybrid --backtest
```

Attach return attribution when `yfinance` is installed:

```bash
counterparty-sentiment news.jsonl \
  --fetch-news \
  --tickers JPM,LMT,NVDA \
  --with-returns \
  --benchmark SPY \
  --horizons 1,3,5,10 \
  --backtest \
  --output results.jsonl
```

### Python research API

```python
from counterparty_sentiment.backtest import backtest_results
from counterparty_sentiment.returns import attach_returns

rows_with_returns = attach_returns(analyzed_rows, price_data, benchmark_prices=spy_prices)
metrics = backtest_results(rows_with_returns, horizon=5)
```

### Limitations and disclaimers

- This is a research prototype, not investment advice or a production trading system.
- The default entity linker is an auditable alias dictionary, not a full NER or knowledge graph.
- The default analyzer is transparent and dependency-light; FinBERT and market data are optional.
- Yahoo Finance availability, licensing, and historical corrections are outside this package's control.
- Backtest metrics do not include transaction costs, borrow fees, slippage, market impact, survivorship bias, or point-in-time universe controls.
- Use out-of-sample testing, data-vendor compliance review, and model-risk controls before any production investment use.

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
- `dimension_scores`: normalized credit, liquidity, systemic, legal/conduct, sanctions, market, and resilience scores.
- `category_scores`: raw weighted category evidence before normalization.
- `severity`: low, medium, or high risk severity.
- `source_reliability` and `recency_weight`: production-oriented score adjustments.
- `extracted_events`: structured events such as downgrade, covenant breach, liquidity stress, sanctions exposure, default warning, or fraud loss exposure.
- `explanation`: short matched-signal explanation for review.
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

## Project structure

```text
.
├── index.html                  # Complete static webpage
├── web/
│   ├── app.js                  # Browser-side NLP, live-news, and stock-pick demo
│   └── styles.css              # Responsive webpage styling
├── src/counterparty_sentiment/ # Python package
│   ├── lexicons.py             # Weighted risk lexicons and source reliability
│   ├── extraction.py           # Structured financial event extraction
│   ├── ml.py                   # Optional FinBERT/transformer adapter
│   ├── ingestion.py            # Local JSONL, RSS, and Yahoo news normalization
│   ├── entity_linking.py       # Auditable company-name-to-ticker mapper
│   ├── market_data.py          # Optional yfinance OHLCV download helpers
│   ├── returns.py              # Forward and abnormal return attribution
│   └── backtest.py             # Signal generation and research metrics
├── scripts/fetch_news.py       # Standalone news ingestion script
├── examples/events.jsonl       # Sample input stream
├── tests/                      # Python and static-site tests
└── docs/architecture.md        # Processing architecture notes
```

## Development

Run the tests with:

```bash
python -m pytest
```

Additional checks used for this project:

```bash
node --check web/app.js
python -m compileall src tests
```

## Roadmap

- Add configurable multi-dimensional lexicon loading from YAML or JSON.
- Add connectors for Kafka, cloud queues, and market/news APIs.
- Add optional transformer-based analyzer implementations behind the same analyzer interface.
- Add dashboards for live counterparty heatmaps and alert triage.
- Add benchmark datasets and drift monitoring for production deployments.
