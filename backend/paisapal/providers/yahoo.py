from __future__ import annotations

from typing import Any

import httpx

from paisapal.providers.base import EvidenceSnapshot, redact_url_secrets

BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart"


class YahooFinanceProvider:
    name = "yahoo"

    def __init__(self, http_client: Any | None = None, timeout: float = 10.0) -> None:
        self.http_client = http_client or httpx
        self.timeout = timeout

    def collect(self, ticker: str) -> list[EvidenceSnapshot]:
        try:
            payload = self._request(ticker)
            result = payload["chart"]["result"][0]
            meta = result.get("meta", {})
            quote = result.get("indicators", {}).get("quote", [{}])[0]
            bars = _bars(result.get("timestamp", []), quote)
            if not bars:
                return [self._error_snapshot(ticker, "Yahoo chart response did not include bars")]
        except Exception as exc:
            return [self._error_snapshot(ticker, str(exc))]

        closes = [bar["close"] for bar in bars if bar["close"] is not None]
        highs = [bar["high"] for bar in bars if bar["high"] is not None]
        lows = [bar["low"] for bar in bars if bar["low"] is not None]
        volumes = [bar["volume"] for bar in bars if bar["volume"] is not None]
        latest_close = closes[-1] if closes else meta.get("regularMarketPrice")
        return [
            EvidenceSnapshot(
                provider=self.name,
                source_type="market",
                status="fresh",
                label="Yahoo Finance chart quote",
                payload={
                    "ticker": meta.get("symbol") or ticker.upper(),
                    "name": meta.get("longName") or meta.get("shortName"),
                    "currency": meta.get("currency"),
                    "exchange": meta.get("exchangeName"),
                    "session": {
                        "price": _float_or_none(meta.get("regularMarketPrice") or latest_close),
                        "previous_close": _float_or_none(meta.get("previousClose")),
                    },
                },
                url=f"{BASE_URL}/{ticker.upper()}",
            ),
            EvidenceSnapshot(
                provider=self.name,
                source_type="technicals",
                status="fresh",
                label="Yahoo Finance daily bars",
                payload={
                    "ticker": ticker.upper(),
                    "latest_close": _float_or_none(latest_close),
                    "sma_20": _moving_average(closes, 20),
                    "sma_50": _moving_average(closes, 50),
                    "range_high": max(highs) if highs else None,
                    "range_low": min(lows) if lows else None,
                    "average_volume": round(sum(volumes) / len(volumes)) if volumes else None,
                    "bars": bars,
                },
                url=f"{BASE_URL}/{ticker.upper()}",
            ),
        ]

    def _request(self, ticker: str) -> dict[str, Any]:
        response = self.http_client.get(
            f"{BASE_URL}/{ticker.upper()}",
            params={"range": "6mo", "interval": "1d"},
            headers={"User-Agent": "Mozilla/5.0 PaisaPal/0.1"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Unexpected Yahoo Finance response")
        return payload

    def _error_snapshot(self, ticker: str, warning: str) -> EvidenceSnapshot:
        return EvidenceSnapshot(
            provider=self.name,
            source_type="provider_status",
            status="error",
            label="Yahoo Finance chart",
            payload={"ticker": ticker.upper()},
            url=f"{BASE_URL}/{ticker.upper()}",
            warnings=[redact_url_secrets(warning)],
        )


def _bars(timestamps: list[Any], quote: dict[str, list[Any]]) -> list[dict[str, Any]]:
    bars = []
    for index, timestamp in enumerate(timestamps):
        bars.append(
            {
                "timestamp": timestamp,
                "open": _float_at(quote, "open", index),
                "high": _float_at(quote, "high", index),
                "low": _float_at(quote, "low", index),
                "close": _float_at(quote, "close", index),
                "volume": _int_at(quote, "volume", index),
            }
        )
    return bars


def _float_at(payload: dict[str, list[Any]], key: str, index: int) -> float | None:
    values = payload.get(key, [])
    return _float_or_none(values[index] if index < len(values) else None)


def _int_at(payload: dict[str, list[Any]], key: str, index: int) -> int | None:
    values = payload.get(key, [])
    return _int_or_none(values[index] if index < len(values) else None)


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
