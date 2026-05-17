from __future__ import annotations

import os
from typing import Any

import httpx

from paisapal.providers.base import EvidenceSnapshot, redact_url_secrets

BASE_URL = "https://api.tiingo.com"


class TiingoProvider:
    name = "tiingo"

    def __init__(self, api_key: str | None = None, http_client: Any | None = None, timeout: float = 10.0) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("TIINGO_API_KEY")
        self.http_client = http_client or httpx
        self.timeout = timeout

    def collect(self, ticker: str) -> list[EvidenceSnapshot]:
        if not self.api_key:
            return [_missing_snapshot(self.name, ticker, "Tiingo")]

        symbol = ticker.upper()
        errors: list[EvidenceSnapshot] = []
        try:
            prices = self._request(f"/tiingo/daily/{symbol}/prices", {"resampleFreq": "daily", "format": "json"})
        except Exception as exc:
            return [self._error_snapshot(ticker, "prices", str(exc))]

        if warning := _provider_warning(prices):
            return [self._error_snapshot(ticker, "prices", warning)]
        try:
            news = self._request("/tiingo/news", {"tickers": symbol, "limit": 10})
        except Exception as exc:
            news = []
            errors.append(self._error_snapshot(ticker, "news", str(exc)))
        if warning := _provider_warning(news):
            news = []
            errors.append(self._error_snapshot(ticker, "news", warning))

        bars = [_bar(row) for row in _rows(prices, 120)]
        bars = [bar for bar in bars if bar["close"] is not None]
        closes = [bar["close"] for bar in bars]
        highs = [bar["high"] for bar in bars if bar["high"] is not None]
        lows = [bar["low"] for bar in bars if bar["low"] is not None]
        volumes = [bar["volume"] for bar in bars if bar["volume"] is not None]
        latest = bars[-1] if bars else {}
        evidence = [
            EvidenceSnapshot(
                provider=self.name,
                source_type="market",
                status="fresh",
                label="Tiingo end-of-day price",
                payload={
                    "ticker": symbol,
                    "session": {
                        "price": latest.get("close"),
                        "open": latest.get("open"),
                        "high": latest.get("high"),
                        "low": latest.get("low"),
                        "volume": latest.get("volume"),
                    },
                },
                url=f"{BASE_URL}/tiingo/daily/{symbol}/prices",
            ),
            EvidenceSnapshot(
                provider=self.name,
                source_type="technicals",
                status="fresh",
                label="Tiingo daily bars",
                payload={
                    "ticker": symbol,
                    "latest_close": latest.get("close"),
                    "sma_20": _moving_average(closes, 20),
                    "sma_50": _moving_average(closes, 50),
                    "range_high": max(highs) if highs else None,
                    "range_low": min(lows) if lows else None,
                    "average_volume": round(sum(volumes) / len(volumes)) if volumes else None,
                    "bars": bars,
                },
                url=f"{BASE_URL}/tiingo/daily/{symbol}/prices",
            ),
        ]
        if _rows(news, 10):
            evidence.append(
                EvidenceSnapshot(
                    provider=self.name,
                    source_type="news_sentiment",
                    status="fresh",
                    label="Tiingo company news",
                    payload={"ticker": symbol, "articles": [_news_article(row) for row in _rows(news, 10)]},
                    url=f"{BASE_URL}/tiingo/news",
                )
            )
        return evidence + errors

    def _request(self, path: str, params: dict[str, Any]) -> Any:
        response = self.http_client.get(
            f"{BASE_URL}{path}",
            params=params,
            headers={"Authorization": f"Token {self.api_key}"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def _error_snapshot(self, ticker: str, endpoint: str, warning: str) -> EvidenceSnapshot:
        return EvidenceSnapshot(
            provider=self.name,
            source_type="provider_status",
            status="error",
            label=f"Tiingo {endpoint}",
            payload={"ticker": ticker.upper(), "endpoint": endpoint},
            url=BASE_URL,
            warnings=[redact_url_secrets(warning)],
        )


def _missing_snapshot(provider: str, ticker: str, label: str) -> EvidenceSnapshot:
    return EvidenceSnapshot(
        provider=provider,
        source_type="provider_status",
        status="missing",
        label=label,
        payload={"ticker": ticker.upper()},
        warnings=["API key is not configured"],
    )


def _provider_warning(payload: Any) -> str | None:
    if isinstance(payload, dict):
        for key in ("detail", "message", "error"):
            if payload.get(key):
                return str(payload[key])
    return None


def _rows(payload: Any, limit: int) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        return []
    return [row for row in payload[:limit] if isinstance(row, dict)]


def _bar(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "date": row.get("date"),
        "open": _float_or_none(row.get("open")),
        "high": _float_or_none(row.get("high")),
        "low": _float_or_none(row.get("low")),
        "close": _float_or_none(row.get("close")),
        "volume": _int_or_none(row.get("volume")),
    }


def _news_article(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": row.get("title"),
        "url": row.get("url"),
        "time_published": row.get("publishedDate"),
        "source": row.get("source"),
        "summary": row.get("description"),
    }


def _moving_average(values: list[float], window: int) -> float | None:
    if len(values) < window:
        return None
    return round(sum(values[-window:]) / window, 4)


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
