"""Optional market data access for news-to-return research."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class PriceBar:
    """One OHLCV observation."""

    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    def to_dict(self) -> dict[str, float | str]:
        return {
            "date": self.date.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }


def fetch_ohlcv(ticker: str, start: datetime | date | str, end: datetime | date | str) -> list[PriceBar]:
    """Download OHLCV data with optional yfinance.

    yfinance is imported lazily so lexicon-only and offline workflows remain
    dependency-light.  Callers can catch RuntimeError and continue without
    return attribution.
    """
    try:
        import yfinance as yf  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("Market data mode requires optional dependency 'yfinance'.") from exc

    frame = yf.download(ticker, start=_date_str(start), end=_date_str(end), progress=False, auto_adjust=False)
    if frame is None or frame.empty:
        return []
    bars: list[PriceBar] = []
    for index, row in frame.iterrows():
        day = index.date() if hasattr(index, "date") else _coerce_date(index)
        bars.append(
            PriceBar(
                date=day,
                open=float(_cell(row, "Open")),
                high=float(_cell(row, "High")),
                low=float(_cell(row, "Low")),
                close=float(_cell(row, "Close")),
                volume=float(_cell(row, "Volume", 0.0)),
            )
        )
    return bars


def fetch_price_window(ticker: str, event_time: datetime, *, pre_days: int = 35, post_days: int = 20) -> list[PriceBar]:
    """Fetch a window around an event timestamp."""
    start = event_time.date() - timedelta(days=pre_days)
    end = event_time.date() + timedelta(days=post_days)
    return fetch_ohlcv(ticker, start, end)


def normalize_price_bars(data: Iterable[PriceBar | Mapping[str, object] | tuple[object, object]]) -> list[PriceBar]:
    """Normalize test fixtures, dictionaries, tuples, or PriceBar objects."""
    bars: list[PriceBar] = []
    for item in data:
        if isinstance(item, PriceBar):
            bars.append(item)
        elif isinstance(item, Mapping):
            close = float(item.get("close", item.get("Close", 0.0)))
            bars.append(
                PriceBar(
                    date=_coerce_date(item.get("date", item.get("Date"))),
                    open=float(item.get("open", item.get("Open", close))),
                    high=float(item.get("high", item.get("High", close))),
                    low=float(item.get("low", item.get("Low", close))),
                    close=close,
                    volume=float(item.get("volume", item.get("Volume", 0.0))),
                )
            )
        else:
            day, close = item
            bars.append(PriceBar(date=_coerce_date(day), open=float(close), high=float(close), low=float(close), close=float(close)))
    return sorted(bars, key=lambda bar: bar.date)


def next_trading_index(bars: Sequence[PriceBar], event_time: datetime | date | str) -> int | None:
    """Return the first bar index on or after the event date."""
    event_date = _coerce_date(event_time)
    for index, bar in enumerate(bars):
        if bar.date >= event_date:
            return index
    return None


def _cell(row: object, name: str, default: float | None = None) -> float:
    try:
        value = row[name]
    except Exception:
        if default is None:
            raise
        return default
    if hasattr(value, "iloc"):
        value = value.iloc[0]
    return float(value)


def _date_str(value: datetime | date | str) -> str:
    return _coerce_date(value).isoformat()


def _coerce_date(value: object) -> date:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).date() if value.tzinfo else value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    raise TypeError(f"Unsupported date value: {value!r}")
