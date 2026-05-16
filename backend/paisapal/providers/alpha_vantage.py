from __future__ import annotations

import os
from typing import Any

import httpx

from paisapal.providers.base import EvidenceSnapshot, redact_url_secrets

BASE_URL = "https://www.alphavantage.co/query"


class AlphaVantageProvider:
    name = "alpha_vantage"

    def __init__(self, api_key: str | None = None, http_client: Any | None = None, timeout: float = 10.0) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("ALPHA_VANTAGE_API_KEY")
        self.http_client = http_client or httpx
        self.timeout = timeout

    def collect(self, ticker: str) -> list[EvidenceSnapshot]:
        if not self.api_key:
            return [
                EvidenceSnapshot(
                    provider=self.name,
                    source_type="provider_status",
                    status="missing",
                    label="Alpha Vantage",
                    payload={"ticker": ticker},
                    warnings=["API key is not configured"],
                )
            ]

        evidence: list[EvidenceSnapshot] = []
        for function, source_type, label in [
            ("TIME_SERIES_DAILY", "market", "Alpha Vantage daily time series"),
            ("OVERVIEW", "fundamentals", "Alpha Vantage company overview"),
            ("EARNINGS", "earnings", "Alpha Vantage earnings"),
            ("NEWS_SENTIMENT", "news_sentiment", "Alpha Vantage news sentiment"),
        ]:
            try:
                payload = self._request(function, ticker)
            except Exception as exc:
                return [self._error_snapshot(ticker, function, str(exc))]

            provider_warning = self._provider_warning(payload)
            if provider_warning:
                return [self._error_snapshot(ticker, function, provider_warning)]

            evidence.append(
                EvidenceSnapshot(
                    provider=self.name,
                    source_type=source_type,
                    status="fresh",
                    label=label,
                    payload=self._normalize(function, ticker, payload),
                    url=BASE_URL,
                )
            )

        return evidence

    def _request(self, function: str, ticker: str) -> dict[str, Any]:
        params = {"function": function, "apikey": self.api_key}
        if function == "NEWS_SENTIMENT":
            params["tickers"] = ticker
        else:
            params["symbol"] = ticker

        response = self.http_client.get(BASE_URL, params=params, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError(f"Unexpected Alpha Vantage response for {function}")
        return payload

    def _normalize(self, function: str, ticker: str, payload: dict[str, Any]) -> dict[str, Any]:
        if function == "TIME_SERIES_DAILY":
            return self._normalize_market(ticker, payload)
        if function == "OVERVIEW":
            return self._normalize_fundamentals(ticker, payload)
        if function == "EARNINGS":
            return self._normalize_earnings(ticker, payload)
        if function == "NEWS_SENTIMENT":
            return self._normalize_news_sentiment(ticker, payload)
        return {"ticker": ticker, "raw": payload}

    def _normalize_market(self, ticker: str, payload: dict[str, Any]) -> dict[str, Any]:
        series = payload.get("Time Series (Daily)", {})
        if not isinstance(series, dict) or not series:
            return {"ticker": ticker, "latest_trading_day": None, "raw": payload}

        latest_trading_day = sorted(series)[-1]
        latest = series.get(latest_trading_day, {})
        return {
            "ticker": ticker,
            "latest_trading_day": latest_trading_day,
            "open": _float_or_none(latest.get("1. open")),
            "high": _float_or_none(latest.get("2. high")),
            "low": _float_or_none(latest.get("3. low")),
            "latest_close": _float_or_none(latest.get("4. close")),
            "volume": _int_or_none(latest.get("5. volume")),
            "last_refreshed": payload.get("Meta Data", {}).get("3. Last Refreshed"),
        }

    def _normalize_fundamentals(self, ticker: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "ticker": payload.get("Symbol") or ticker,
            "name": payload.get("Name"),
            "sector": payload.get("Sector"),
            "industry": payload.get("Industry"),
            "market_cap": _int_or_none(payload.get("MarketCapitalization")),
            "pe_ratio": _float_or_none(payload.get("PERatio")),
            "eps": _float_or_none(payload.get("EPS")),
        }

    def _normalize_earnings(self, ticker: str, payload: dict[str, Any]) -> dict[str, Any]:
        quarterly = payload.get("quarterlyEarnings", [])
        if not isinstance(quarterly, list):
            quarterly = []
        return {
            "ticker": payload.get("symbol") or ticker,
            "quarterly_earnings": [
                {
                    "fiscal_date_ending": item.get("fiscalDateEnding"),
                    "reported_eps": _float_or_none(item.get("reportedEPS")),
                    "estimated_eps": _float_or_none(item.get("estimatedEPS")),
                    "surprise": _float_or_none(item.get("surprise")),
                    "surprise_percentage": _float_or_none(item.get("surprisePercentage")),
                }
                for item in quarterly[:8]
                if isinstance(item, dict)
            ],
        }

    def _normalize_news_sentiment(self, ticker: str, payload: dict[str, Any]) -> dict[str, Any]:
        feed = payload.get("feed", [])
        if not isinstance(feed, list):
            feed = []
        return {
            "ticker": ticker,
            "articles": [
                {
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "time_published": item.get("time_published"),
                    "sentiment_label": item.get("overall_sentiment_label"),
                    "sentiment_score": _float_or_none(item.get("overall_sentiment_score")),
                }
                for item in feed[:10]
                if isinstance(item, dict)
            ],
        }

    def _provider_warning(self, payload: dict[str, Any]) -> str | None:
        for key in ("Note", "Information", "Error Message"):
            value = payload.get(key)
            if value:
                return str(value)
        return None

    def _error_snapshot(self, ticker: str, function: str, warning: str) -> EvidenceSnapshot:
        return EvidenceSnapshot(
            provider=self.name,
            source_type="provider_status",
            status="error",
            label=f"Alpha Vantage {function}",
            payload={"ticker": ticker, "function": function},
            url=BASE_URL,
            warnings=[redact_url_secrets(warning)],
        )


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
