from __future__ import annotations

import re

_TICKER_PATTERN = re.compile(r"^[A-Z][A-Z0-9.-]{0,9}$")


def parse_tickers(raw: str) -> list[str]:
    candidates = [value.strip().upper() for value in re.split(r"[\s,]+", raw) if value.strip()]
    if not candidates:
        raise ValueError("Enter at least one ticker")

    tickers: list[str] = []
    seen: set[str] = set()
    for ticker in candidates:
        if not _TICKER_PATTERN.fullmatch(ticker):
            raise ValueError(f"Invalid ticker: {ticker}")
        if ticker not in seen:
            tickers.append(ticker)
            seen.add(ticker)
    return tickers
