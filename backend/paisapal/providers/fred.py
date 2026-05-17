from __future__ import annotations

import os
from typing import Any

import httpx

from paisapal.providers.base import EvidenceSnapshot, redact_url_secrets

BASE_URL = "https://api.stlouisfed.org/fred"
DEFAULT_SERIES_IDS = ["FEDFUNDS", "CPIAUCSL", "UNRATE", "DGS10"]


class FredProvider:
    name = "fred"

    def __init__(
        self,
        api_key: str | None = None,
        http_client: Any | None = None,
        timeout: float = 10.0,
        series_ids: list[str] | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("FRED_API_KEY")
        self.http_client = http_client or httpx
        self.timeout = timeout
        self.series_ids = series_ids or DEFAULT_SERIES_IDS

    def collect(self, ticker: str) -> list[EvidenceSnapshot]:
        if not self.api_key:
            return [_missing_snapshot(self.name, ticker, "FRED")]

        evidence = []
        for series_id in self.series_ids:
            try:
                payload = self._request(series_id)
            except Exception as exc:
                return [self._error_snapshot(ticker, series_id, str(exc))]
            if warning := _provider_warning(payload):
                return [self._error_snapshot(ticker, series_id, warning)]
            observations = [
                {"date": row.get("date"), "value": _float_or_none(row.get("value"))}
                for row in _rows(payload.get("observations", []), 24)
            ]
            observations = [row for row in observations if row["value"] is not None]
            evidence.append(
                EvidenceSnapshot(
                    provider=self.name,
                    source_type="macro",
                    status="fresh",
                    label=f"FRED macro series {series_id}",
                    payload={
                        "ticker": ticker.upper(),
                        "series_id": series_id,
                        "latest": observations[0] if observations else None,
                        "observations": observations,
                    },
                    url=f"{BASE_URL}/series/observations",
                )
            )
        return evidence

    def _request(self, series_id: str) -> dict[str, Any]:
        response = self.http_client.get(
            f"{BASE_URL}/series/observations",
            params={
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": 24,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError(f"Unexpected FRED response for {series_id}")
        return payload

    def _error_snapshot(self, ticker: str, series_id: str, warning: str) -> EvidenceSnapshot:
        return EvidenceSnapshot(
            provider=self.name,
            source_type="provider_status",
            status="error",
            label=f"FRED {series_id}",
            payload={"ticker": ticker.upper(), "series_id": series_id},
            url=f"{BASE_URL}/series/observations",
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


def _provider_warning(payload: dict[str, Any]) -> str | None:
    for key in ("error_message", "message", "error"):
        if payload.get(key):
            return str(payload[key])
    return None


def _rows(payload: Any, limit: int) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        return []
    return [row for row in payload[:limit] if isinstance(row, dict)]


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
