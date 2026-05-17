from __future__ import annotations

import os
from datetime import date, timedelta
from typing import Any

import httpx

from paisapal.providers.base import EvidenceSnapshot, redact_url_secrets

BASE_URL = "https://finnhub.io/api/v1"


class FinnhubProvider:
    name = "finnhub"

    def __init__(
        self,
        api_key: str | None = None,
        http_client: Any | None = None,
        timeout: float = 10.0,
        end_date: date | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("FINNHUB_API_KEY")
        self.http_client = http_client or httpx
        self.timeout = timeout
        self.end_date = end_date or date.today()

    def collect(self, ticker: str) -> list[EvidenceSnapshot]:
        if not self.api_key:
            return [_missing_snapshot(self.name, ticker, "Finnhub")]

        symbol = ticker.upper()
        start_date = self.end_date - timedelta(days=30)
        payloads: dict[str, Any] = {}
        errors: list[EvidenceSnapshot] = []
        try:
            payloads["quote"] = self._request("/quote", {"symbol": symbol})
        except Exception as exc:
            if _is_auth_error(exc):
                return [_missing_endpoint_snapshot(ticker, "quote", str(exc))]
            return [self._error_snapshot(ticker, "quote", str(exc))]

        for endpoint, path, params in [
            ("earnings", "/stock/earnings", {"symbol": symbol, "limit": 8}),
            (
                "company-news",
                "/company-news",
                {"symbol": symbol, "from": start_date.isoformat(), "to": self.end_date.isoformat()},
            ),
            ("option-chain", "/stock/option-chain", {"symbol": symbol}),
        ]:
            try:
                payload = self._request(path, params)
            except Exception as exc:
                if _is_auth_error(exc):
                    errors.append(_missing_endpoint_snapshot(ticker, endpoint, str(exc)))
                    continue
                errors.append(self._error_snapshot(ticker, endpoint, str(exc)))
                continue
            if warning := _provider_warning(payload):
                if _is_auth_warning(warning):
                    errors.append(_missing_endpoint_snapshot(ticker, endpoint, warning))
                    continue
                errors.append(self._error_snapshot(ticker, endpoint, warning))
                continue
            payloads[endpoint] = payload

        quote = payloads["quote"]
        evidence = [
            EvidenceSnapshot(
                provider=self.name,
                source_type="market",
                status="fresh",
                label="Finnhub quote",
                payload={
                    "ticker": symbol,
                    "session": {
                        "price": _float_or_none(quote.get("c")),
                        "previous_close": _float_or_none(quote.get("pc")),
                        "open": _float_or_none(quote.get("o")),
                        "high": _float_or_none(quote.get("h")),
                        "low": _float_or_none(quote.get("l")),
                        "timestamp": quote.get("t"),
                    },
                },
                url=f"{BASE_URL}/quote",
            ),
        ]
        if "earnings" in payloads:
            evidence.append(
                EvidenceSnapshot(
                    provider=self.name,
                    source_type="earnings",
                    status="fresh",
                    label="Finnhub company earnings",
                    payload={"ticker": symbol, "earnings": [_earnings_row(row) for row in _rows(payloads["earnings"], 8)]},
                    url=f"{BASE_URL}/stock/earnings",
                )
            )
        if "company-news" in payloads:
            evidence.append(
                EvidenceSnapshot(
                    provider=self.name,
                    source_type="news_sentiment",
                    status="fresh",
                    label="Finnhub company news",
                    payload={"ticker": symbol, "articles": [_news_article(row) for row in _rows(payloads["company-news"], 10)]},
                    url=f"{BASE_URL}/company-news",
                )
            )
        if "option-chain" in payloads:
            evidence.append(
                EvidenceSnapshot(
                    provider=self.name,
                    source_type="options",
                    status="fresh",
                    label="Finnhub option chain",
                    payload={"ticker": symbol, "contracts": _option_contracts(payloads["option-chain"])},
                    url=f"{BASE_URL}/stock/option-chain",
                )
            )
        return evidence + errors

    def _request(self, path: str, params: dict[str, Any]) -> Any:
        response = self.http_client.get(
            f"{BASE_URL}{path}",
            params={**params, "token": self.api_key},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def _error_snapshot(self, ticker: str, endpoint: str, warning: str) -> EvidenceSnapshot:
        return EvidenceSnapshot(
            provider=self.name,
            source_type="provider_status",
            status="error",
            label=f"Finnhub {endpoint}",
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


def _missing_endpoint_snapshot(ticker: str, endpoint: str, warning: str) -> EvidenceSnapshot:
    return EvidenceSnapshot(
        provider="finnhub",
        source_type="provider_status",
        status="missing",
        label=f"Finnhub {endpoint}",
        payload={"ticker": ticker.upper(), "endpoint": endpoint},
        url=BASE_URL,
        warnings=[redact_url_secrets(warning)],
    )


def _provider_warning(payload: Any) -> str | None:
    if isinstance(payload, dict):
        for key in ("error", "message", "detail"):
            if payload.get(key):
                return str(payload[key])
    return None


def _is_auth_warning(warning: str) -> bool:
    normalized = warning.lower()
    return any(
        token in normalized
        for token in (
            "forbidden",
            "unauthorized",
            "payment required",
            "invalid api key",
            "permission denied",
        )
    )


def _is_auth_error(exc: Exception) -> bool:
    return isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in {401, 403}


def _rows(payload: Any, limit: int) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        return []
    return [row for row in payload[:limit] if isinstance(row, dict)]


def _earnings_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "period": row.get("period"),
        "eps_actual": _float_or_none(row.get("actual")),
        "eps_estimated": _float_or_none(row.get("estimate")),
        "surprise": _float_or_none(row.get("surprise")),
        "surprise_percentage": _float_or_none(row.get("surprisePercent")),
    }


def _news_article(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": row.get("headline"),
        "url": row.get("url"),
        "time_published": row.get("datetime"),
        "source": row.get("source"),
        "summary": row.get("summary"),
    }


def _option_contracts(payload: Any) -> list[dict[str, Any]]:
    contracts = []
    data = payload.get("data", []) if isinstance(payload, dict) else []
    for expiry in _rows(data, 4):
        expiration_date = expiry.get("expirationDate")
        option_groups = expiry.get("options", {})
        if not isinstance(option_groups, dict):
            continue
        for contract_type, rows in option_groups.items():
            for row in _rows(rows, 20):
                contracts.append(
                    {
                        "ticker": row.get("symbol"),
                        "contract_type": str(contract_type).lower(),
                        "strike_price": _float_or_none(row.get("strike")),
                        "expiration_date": expiration_date,
                        "last_price": _float_or_none(row.get("lastPrice")),
                        "bid": _float_or_none(row.get("bid")),
                        "ask": _float_or_none(row.get("ask")),
                        "volume": _int_or_none(row.get("volume")),
                        "open_interest": _int_or_none(row.get("openInterest")),
                        "implied_volatility": _float_or_none(row.get("impliedVolatility")),
                    }
                )
    return contracts[:40]


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
