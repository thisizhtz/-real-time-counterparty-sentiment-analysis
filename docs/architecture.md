# Architecture

```mermaid
flowchart LR
    A[News, filings, chat, tickets] --> B[JSONL or stream adapter]
    B --> C[TextEvent normalization]
    C --> D[SentimentAnalyzer]
    D --> E[SentimentResult]
    E --> F[Rolling counterparty window]
    F --> G[Alerts, dashboards, risk workflows]
```

## Components

1. **Ingestion boundary**: the CLI currently consumes newline-delimited JSON. Production adapters can wrap the same `TextEvent` model for queues or APIs.
2. **Analyzer**: `SentimentAnalyzer` applies auditable lexicons for positive indicators, negative indicators, intensity/negation cues, risk flags, and six dimensions: credit, liquidity, systemic, legal/conduct, market, and resilience.
3. **Streaming state**: `SentimentStream` stores a bounded rolling window per counterparty and exposes snapshots with averaged sentiment and dimension scores for downstream routing.
4. **Output boundary**: results are JSON-serializable and include event-level signals, severity, explanations, dimension scores, and optional rolling snapshots.

## Operational considerations

- Keep source text and generated scores traceable for model-risk review.
- Treat the lexicon and dimension weights as configuration in regulated environments and review changes through normal change-management controls.
- Monitor source-specific false positives, especially around negated risk terms, systemic-risk language, and legal boilerplate.
- Use this baseline as an explainable first pass before adding heavier model-backed scoring.
