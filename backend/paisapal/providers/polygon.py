from __future__ import annotations

import os
from datetime import date, timedelta
from typing import Any

import httpx

from paisapal.providers.base import EvidenceSnapshot

BASE_URL = "https://api.polygon.io"


class PolygonProvider:
    name = "polygon"

    def __init__(
        self,
        api_key: str | None = None,
        http_client: Any | None = None,
        timeout: float = 10.0,
        end_date: date | None = None,
        lookback_days: int = 120,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("POLYGON_API_KEY")
        self.http_client = http_client or httpx
        self.timeout = timeout
        self.end_date = end_date or date.today()
        self.lookback_days = lookback_days

    def collect(self, ticker: str) -> list[EvidenceSnapshot]:
        if not self.api_key:
            return [
                EvidenceSnapshot(
                    provider=self.name,
                    source_type="provider_status",
                    status="missing",
                    label="Polygon",
                    payload={"ticker": ticker},
                    warnings=["API key is not configured"],
                )
            ]

        start_date = self.end_date - timedelta(days=self.lookback_days)
        requests = [
            ("ticker_details", f"/v3/reference/tickers/{ticker}", {}),
            ("stock_snapshot", "/v3/snapshot", {"ticker": ticker, "type": "stocks", "limit": 1}),
            (
                "daily_aggregates",
                f"/v2/aggs/ticker/{ticker}/range/1/day/{start_date.isoformat()}/{self.end_date.isoformat()}",
                {"adjusted": True, "sort": "asc", "limit": self.lookback_days},
            ),
            ("options_snapshot", f"/v3/snapshot/options/{ticker}", {"limit": 20}),
        ]
        payloads: dict[str, Any] = {}
        for endpoint, path, params in requests:
            try:
                payload = self._request(path, params)
            except Exception as exc:
                return [self._error_snapshot(ticker, endpoint, path, str(exc))]

            provider_warning = self._provider_warning(payload)
            if provider_warning:
                return [self._error_snapshot(ticker, endpoint, path, provider_warning)]
            payloads[endpoint] = payload

        return [
            EvidenceSnapshot(
                provider=self.name,
                source_type="market",
                status="fresh",
                label="Polygon stock snapshot",
                payload=self._normalize_market(ticker, payloads["ticker_details"], payloads["stock_snapshot"]),
                url=f"{BASE_URL}/v3/snapshot",
            ),
            EvidenceSnapshot(
                provider=self.name,
                source_type="technicals",
                status="fresh",
                label="Polygon daily aggregates",
                payload=self._normalize_technicals(ticker, payloads["daily_aggregates"]),
                url=f"{BASE_URL}/v2/aggs/ticker/{ticker}/range/1/day/{start_date.isoformat()}/{self.end_date.isoformat()}",
            ),
            EvidenceSnapshot(
                provider=self.name,
                source_type="options",
                status="fresh",
                label="Polygon options snapshot",
                payload=self._normalize_options(ticker, payloads["options_snapshot"]),
                url=f"{BASE_URL}/v3/snapshot/options/{ticker}",
            ),
        ]

    def _request(self, path: str, params: dict[str, Any]) -> Any:
        request_params = {**params, "apiKey": self.api_key}
        response = self.http_client.get(f"{BASE_URL}{path}", params=request_params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def _normalize_market(self, ticker: str, details_payload: Any, snapshot_payload: Any) -> dict[str, Any]:
        details = _results(details_payload, default={})
        snapshot = _first_result(snapshot_payload)
        session = snapshot.get("session", {})
        last_trade = snapshot.get("last_trade", {})
        return {
            "ticker": details.get("ticker") or snapshot.get("ticker") or ticker,
            "name": details.get("name"),
            "market": details.get("market"),
            "primary_exchange": details.get("primary_exchange"),
            "type": details.get("type"),
            "market_cap": _int_or_none(details.get("market_cap")),
            "industry": details.get("sic_description"),
            "session": {
                "price": _float_or_none(session.get("price")),
                "change": _float_or_none(session.get("change")),
                "change_percent": _float_or_none(session.get("change_percent")),
                "volume": _int_or_none(session.get("volume")),
                "previous_close": _float_or_none(session.get("previous_close")),
            },
            "last_trade": {
                "price": _float_or_none(last_trade.get("price")),
                "sip_timestamp": last_trade.get("sip_timestamp"),
            },
        }

    def _normalize_technicals(self, ticker: str, payload: Any) -> dict[str, Any]:
        bars = _rows(_results(payload, default=[]), limit=self.lookback_days)
        closes = [_float_or_none(item.get("c")) for item in bars]
        closes = [value for value in closes if value is not None]
        highs = [_float_or_none(item.get("h")) for item in bars]
        highs = [value for value in highs if value is not None]
        lows = [_float_or_none(item.get("l")) for item in bars]
        lows = [value for value in lows if value is not None]
        volumes = [_int_or_none(item.get("v")) for item in bars]
        volumes = [value for value in volumes if value is not None]
        return {
            "ticker": ticker,
            "latest_close": closes[-1] if closes else None,
            "sma_20": _moving_average(closes, 20),
            "sma_50": _moving_average(closes, 50),
            "range_high": max(highs) if highs else None,
            "range_low": min(lows) if lows else None,
            "average_volume": round(sum(volumes) / len(volumes)) if volumes else None,
            "bars": [
                {
                    "timestamp": item.get("t"),
                    "open": _float_or_none(item.get("o")),
                    "high": _float_or_none(item.get("h")),
                    "low": _float_or_none(item.get("l")),
                    "close": _float_or_none(item.get("c")),
                    "volume": _int_or_none(item.get("v")),
                }
                for item in bars
            ],
        }

    def _normalize_options(self, ticker: str, payload: Any) -> dict[str, Any]:
        rows = _rows(_results(payload, default=[]), limit=20)
        return {
            "ticker": ticker,
            "contracts": [
                {
                    "ticker": item.get("details", {}).get("ticker"),
                    "contract_type": item.get("details", {}).get("contract_type"),
                    "strike_price": _float_or_none(item.get("details", {}).get("strike_price")),
                    "expiration_date": item.get("details", {}).get("expiration_date"),
                    "implied_volatility": _float_or_none(item.get("implied_volatility")),
                    "open_interest": _int_or_none(item.get("open_interest")),
                    "break_even_price": _float_or_none(item.get("break_even_price")),
                    "delta": _float_or_none(item.get("greeks", {}).get("delta")),
                    "gamma": _float_or_none(item.get("greeks", {}).get("gamma")),
                    "theta": _float_or_none(item.get("greeks", {}).get("theta")),
                    "vega": _float_or_none(item.get("greeks", {}).get("vega")),
                    "day_change": _float_or_none(item.get("day", {}).get("change")),
                    "day_change_percent": _float_or_none(item.get("day", {}).get("change_percent")),
                    "day_volume": _int_or_none(item.get("day", {}).get("volume")),
                    "underlying_price": _float_or_none(item.get("underlying_asset", {}).get("price")),
                }
                for item in rows
            ],
        }

    def _provider_warning(self, payload: Any) -> str | None:
        if not isinstance(payload, dict):
            return None
        status = payload.get("status")
        if status in {"ERROR", "NOT_AUTHORIZED"}:
            return str(payload.get("error") or payload.get("message") or status)
        if payload.get("error"):
            return str(payload["error"])
        return None

    def _error_snapshot(self, ticker: str, endpoint: str, path: str, warning: str) -> EvidenceSnapshot:
        return EvidenceSnapshot(
            provider=self.name,
            source_type="provider_status",
            status="error",
            label=f"Polygon {endpoint}",
            payload={"ticker": ticker, "endpoint": endpoint},
            url=f"{BASE_URL}{path}",
            warnings=[warning],
        )


def _results(payload: Any, default: Any) -> Any:
    if isinstance(payload, dict):
        return payload.get("results", default)
    return default


def _rows(payload: Any, limit: int) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        return []
    return [item for item in payload[:limit] if isinstance(item, dict)]


def _first_result(payload: Any) -> dict[str, Any]:
    results = _results(payload, default=[])
    if isinstance(results, list):
        rows = _rows(results, limit=1)
        return rows[0] if rows else {}
    if isinstance(results, dict):
        return results
    return {}


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
