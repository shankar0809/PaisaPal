from __future__ import annotations

import os
from typing import Any

import httpx

from paisapal.providers.base import EvidenceSnapshot, redact_url_secrets

BASE_URL = "https://financialmodelingprep.com/stable"


class FmpProvider:
    name = "fmp"

    def __init__(self, api_key: str | None = None, http_client: Any | None = None, timeout: float = 10.0) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("FMP_API_KEY")
        self.http_client = http_client or httpx
        self.timeout = timeout

    def collect(self, ticker: str) -> list[EvidenceSnapshot]:
        if not self.api_key:
            return [
                EvidenceSnapshot(
                    provider=self.name,
                    source_type="provider_status",
                    status="missing",
                    label="Financial Modeling Prep",
                    payload={"ticker": ticker},
                    warnings=["API key is not configured"],
                )
            ]

        endpoints = [
            ("profile", None),
            ("income-statement", 4),
            ("balance-sheet-statement", 4),
            ("cash-flow-statement", 4),
            ("ratios", 4),
            ("key-metrics", 4),
            ("financial-scores", None),
            ("earnings", 8),
        ]
        payloads: dict[str, Any] = {}
        errors: list[EvidenceSnapshot] = []
        for endpoint, limit in endpoints:
            try:
                payload = self._request(endpoint, ticker, limit=limit)
            except Exception as exc:
                error = self._error_snapshot(ticker, endpoint, str(exc))
                if not payloads:
                    return [error]
                errors.append(error)
                continue

            provider_warning = self._provider_warning(payload)
            if provider_warning:
                error = self._error_snapshot(ticker, endpoint, provider_warning)
                if not payloads:
                    return [error]
                errors.append(error)
                continue
            payloads[endpoint] = payload

        evidence: list[EvidenceSnapshot] = []
        if "profile" in payloads:
            evidence.append(
                EvidenceSnapshot(
                    provider=self.name,
                    source_type="fundamentals",
                    status="fresh",
                    label="FMP company profile",
                    payload=self._normalize_fundamentals(ticker, payloads["profile"]),
                    url=f"{BASE_URL}/profile",
                )
            )
        if {
            "income-statement",
            "balance-sheet-statement",
            "cash-flow-statement",
        }.issubset(payloads):
            evidence.append(
                EvidenceSnapshot(
                    provider=self.name,
                    source_type="financials",
                    status="fresh",
                    label="FMP financial statements",
                    payload=self._normalize_financials(
                        ticker,
                        payloads["income-statement"],
                        payloads["balance-sheet-statement"],
                        payloads["cash-flow-statement"],
                    ),
                    url=f"{BASE_URL}/income-statement",
                )
            )
        if {"ratios", "key-metrics", "financial-scores"}.issubset(payloads):
            evidence.append(
                EvidenceSnapshot(
                    provider=self.name,
                    source_type="ratios",
                    status="fresh",
                    label="FMP ratios and financial scores",
                    payload=self._normalize_ratios(ticker, payloads["ratios"], payloads["key-metrics"], payloads["financial-scores"]),
                    url=f"{BASE_URL}/ratios",
                )
            )
        if "earnings" in payloads:
            evidence.append(
                EvidenceSnapshot(
                    provider=self.name,
                    source_type="earnings",
                    status="fresh",
                    label="FMP earnings",
                    payload=self._normalize_earnings(ticker, payloads["earnings"]),
                    url=f"{BASE_URL}/earnings",
                )
            )
        return evidence + errors

    def _request(self, endpoint: str, ticker: str, limit: int | None = None) -> Any:
        params: dict[str, Any] = {"symbol": ticker, "apikey": self.api_key}
        if limit is not None:
            params["limit"] = limit
        response = self.http_client.get(f"{BASE_URL}/{endpoint}", params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def _normalize_fundamentals(self, ticker: str, payload: Any) -> dict[str, Any]:
        profile = _first_row(payload)
        return {
            "ticker": profile.get("symbol") or ticker,
            "name": profile.get("companyName"),
            "sector": profile.get("sector"),
            "industry": profile.get("industry"),
            "price": _float_or_none(profile.get("price")),
            "beta": _float_or_none(profile.get("beta")),
            "market_cap": _int_or_none(profile.get("mktCap")),
            "description": profile.get("description"),
        }

    def _normalize_financials(self, ticker: str, income: Any, balance: Any, cash_flow: Any) -> dict[str, Any]:
        return {
            "ticker": ticker,
            "income_statements": [
                {
                    "date": item.get("date"),
                    "revenue": _int_or_none(item.get("revenue")),
                    "gross_profit": _int_or_none(item.get("grossProfit")),
                    "operating_income": _int_or_none(item.get("operatingIncome")),
                    "net_income": _int_or_none(item.get("netIncome")),
                    "eps": _float_or_none(item.get("eps")),
                }
                for item in _rows(income, limit=4)
            ],
            "balance_sheets": [
                {
                    "date": item.get("date"),
                    "cash_and_equivalents": _int_or_none(item.get("cashAndCashEquivalents")),
                    "total_debt": _int_or_none(item.get("totalDebt")),
                    "total_assets": _int_or_none(item.get("totalAssets")),
                    "total_liabilities": _int_or_none(item.get("totalLiabilities")),
                    "stockholders_equity": _int_or_none(item.get("totalStockholdersEquity")),
                }
                for item in _rows(balance, limit=4)
            ],
            "cash_flows": [
                {
                    "date": item.get("date"),
                    "operating_cash_flow": _int_or_none(item.get("operatingCashFlow")),
                    "capital_expenditure": _int_or_none(item.get("capitalExpenditure")),
                    "free_cash_flow": _int_or_none(item.get("freeCashFlow")),
                }
                for item in _rows(cash_flow, limit=4)
            ],
        }

    def _normalize_ratios(self, ticker: str, ratios: Any, key_metrics: Any, financial_scores: Any) -> dict[str, Any]:
        return {
            "ticker": ticker,
            "ratios": [
                {
                    "date": item.get("date"),
                    "gross_profit_margin": _float_or_none(item.get("grossProfitMargin")),
                    "net_profit_margin": _float_or_none(item.get("netProfitMargin")),
                    "current_ratio": _float_or_none(item.get("currentRatio")),
                    "debt_equity_ratio": _float_or_none(item.get("debtEquityRatio")),
                    "price_earnings_ratio": _float_or_none(item.get("priceEarningsRatio")),
                }
                for item in _rows(ratios, limit=4)
            ],
            "key_metrics": [
                {
                    "date": item.get("date"),
                    "revenue_per_share": _float_or_none(item.get("revenuePerShare")),
                    "net_income_per_share": _float_or_none(item.get("netIncomePerShare")),
                    "free_cash_flow_per_share": _float_or_none(item.get("freeCashFlowPerShare")),
                    "pe_ratio": _float_or_none(item.get("peRatio")),
                    "enterprise_value": _int_or_none(item.get("enterpriseValue")),
                }
                for item in _rows(key_metrics, limit=4)
            ],
            "financial_scores": self._normalize_financial_scores(financial_scores),
        }

    def _normalize_financial_scores(self, payload: Any) -> dict[str, Any]:
        scores = _first_row(payload)
        return {
            "altman_z_score": _float_or_none(scores.get("altmanZScore")),
            "piotroski_score": _int_or_none(scores.get("piotroskiScore")),
            "working_capital": _int_or_none(scores.get("workingCapital")),
        }

    def _normalize_earnings(self, ticker: str, payload: Any) -> dict[str, Any]:
        return {
            "ticker": ticker,
            "earnings": [
                {
                    "date": item.get("date"),
                    "eps_actual": _float_or_none(item.get("epsActual")),
                    "eps_estimated": _float_or_none(item.get("epsEstimated")),
                    "revenue_actual": _int_or_none(item.get("revenueActual")),
                    "revenue_estimated": _int_or_none(item.get("revenueEstimated")),
                }
                for item in _rows(payload, limit=8)
            ],
        }

    def _provider_warning(self, payload: Any) -> str | None:
        if isinstance(payload, dict):
            for key in ("Error Message", "error", "message", "Information"):
                value = payload.get(key)
                if value:
                    return str(value)
        return None

    def _error_snapshot(self, ticker: str, endpoint: str, warning: str) -> EvidenceSnapshot:
        return EvidenceSnapshot(
            provider=self.name,
            source_type="provider_status",
            status="error",
            label=f"Financial Modeling Prep {endpoint}",
            payload={"ticker": ticker, "endpoint": endpoint},
            url=f"{BASE_URL}/{endpoint}",
            warnings=[redact_url_secrets(warning)],
        )


def _rows(payload: Any, limit: int) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        return []
    return [item for item in payload[:limit] if isinstance(item, dict)]


def _first_row(payload: Any) -> dict[str, Any]:
    rows = _rows(payload, limit=1)
    return rows[0] if rows else {}


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
