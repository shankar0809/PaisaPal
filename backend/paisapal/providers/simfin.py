from __future__ import annotations

import os
from typing import Any

import httpx

from paisapal.providers.base import EvidenceSnapshot, redact_url_secrets

BASE_URL = "https://backend.simfin.com/api/v3"


class SimFinProvider:
    name = "simfin"

    def __init__(self, api_key: str | None = None, http_client: Any | None = None, timeout: float = 10.0) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("SIMFIN_API_KEY")
        self.http_client = http_client or httpx
        self.timeout = timeout

    def collect(self, ticker: str) -> list[EvidenceSnapshot]:
        if not self.api_key:
            return [_missing_snapshot(self.name, ticker, "SimFin")]

        symbol = ticker.upper()
        try:
            company_payload = self._request("/companies/general/compact", {"ticker": symbol})
        except Exception as exc:
            if _is_auth_error(exc):
                return [_missing_endpoint_snapshot(ticker, "companies", str(exc))]
            return [self._error_snapshot(ticker, "request", str(exc))]

        if warning := _provider_warning(company_payload):
            if _is_auth_warning(warning):
                return [_missing_endpoint_snapshot(ticker, "companies", warning)]
            return [self._error_snapshot(ticker, "companies", warning)]

        try:
            statements_payload = self._request("/companies/statements/compact", {"ticker": symbol, "statements": "pl,bs,cf"})
        except Exception as exc:
            if _is_auth_error(exc):
                return [_first_company_evidence(ticker, company_payload), _missing_endpoint_snapshot(ticker, "statements", str(exc))]
            return [self._error_snapshot(ticker, "request", str(exc))]

        if warning := _provider_warning(statements_payload):
            if _is_auth_warning(warning):
                return [_first_company_evidence(ticker, company_payload), _missing_endpoint_snapshot(ticker, "statements", warning)]
            return [self._error_snapshot(ticker, "statements", warning)]

        company = _first_row(company_payload)
        statement = _first_statement(statements_payload)
        income = statement.get("incomeStatement", {})
        balance = statement.get("balanceSheet", {})
        cash_flow = statement.get("cashFlow", {})
        revenue = _int_or_none(income.get("Revenue"))
        gross_profit = _int_or_none(income.get("Gross Profit"))
        net_income = _int_or_none(income.get("Net Income"))
        assets = _int_or_none(balance.get("Total Assets"))
        liabilities = _int_or_none(balance.get("Total Liabilities"))
        return [
            EvidenceSnapshot(
                provider=self.name,
                source_type="fundamentals",
                status="fresh",
                label="SimFin company fundamentals",
                payload={
                    "ticker": company.get("ticker") or symbol,
                    "name": company.get("name"),
                    "sector": company.get("sector"),
                    "industry": company.get("industry"),
                    "market": company.get("market"),
                    "description": company.get("companyDescription"),
                },
                url=f"{BASE_URL}/companies/general/compact",
            ),
            EvidenceSnapshot(
                provider=self.name,
                source_type="financials",
                status="fresh",
                label="SimFin financial statements",
                payload={
                    "ticker": symbol,
                    "period": statement.get("period"),
                    "fiscal_year": statement.get("fyear"),
                    "income_statement": {
                        "revenue": revenue,
                        "gross_profit": gross_profit,
                        "net_income": net_income,
                    },
                    "balance_sheet": {
                        "assets": assets,
                        "liabilities": liabilities,
                        "equity": _int_or_none(balance.get("Total Equity")),
                    },
                    "cash_flow": {
                        "operating_cash_flow": _int_or_none(cash_flow.get("Net Cash from Operating Activities")),
                        "capital_expenditure": _int_or_none(cash_flow.get("Capital Expenditure")),
                    },
                },
                url=f"{BASE_URL}/companies/statements/compact",
            ),
            EvidenceSnapshot(
                provider=self.name,
                source_type="ratios",
                status="fresh",
                label="SimFin derived ratios",
                payload={
                    "ticker": symbol,
                    "gross_margin": _ratio(gross_profit, revenue),
                    "net_margin": _ratio(net_income, revenue),
                    "debt_to_assets": _ratio(liabilities, assets),
                },
                url=f"{BASE_URL}/companies/statements/compact",
            ),
        ]

    def _request(self, path: str, params: dict[str, Any]) -> Any:
        response = self.http_client.get(
            f"{BASE_URL}{path}",
            params={**params, "api-key": self.api_key},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def _error_snapshot(self, ticker: str, endpoint: str, warning: str) -> EvidenceSnapshot:
        return EvidenceSnapshot(
            provider=self.name,
            source_type="provider_status",
            status="error",
            label=f"SimFin {endpoint}",
            payload={"ticker": ticker.upper(), "endpoint": endpoint},
            url=BASE_URL,
            warnings=[redact_url_secrets(warning)],
        )


def _first_company_evidence(ticker: str, payload: Any) -> EvidenceSnapshot:
    company = _first_row(payload)
    return EvidenceSnapshot(
        provider="simfin",
        source_type="fundamentals",
        status="fresh",
        label="SimFin company fundamentals",
        payload={
            "ticker": company.get("ticker") or ticker.upper(),
            "name": company.get("name"),
            "sector": company.get("sector"),
            "industry": company.get("industry"),
            "market": company.get("market"),
            "description": company.get("companyDescription"),
        },
        url=f"{BASE_URL}/companies/general/compact",
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
        provider="simfin",
        source_type="provider_status",
        status="missing",
        label=f"SimFin {endpoint}",
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


def _first_row(payload: Any) -> dict[str, Any]:
    if isinstance(payload, list):
        rows = [row for row in payload if isinstance(row, dict)]
        return rows[0] if rows else {}
    if isinstance(payload, dict):
        return payload
    return {}


def _first_statement(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        statements = payload.get("statements", [])
        if isinstance(statements, list):
            rows = [row for row in statements if isinstance(row, dict)]
            return rows[0] if rows else {}
    return {}


def _ratio(numerator: int | None, denominator: int | None) -> float | None:
    if numerator is None or denominator in {None, 0}:
        return None
    return round(numerator / denominator, 4)


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
