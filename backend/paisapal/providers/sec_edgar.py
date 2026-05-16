from __future__ import annotations

import os
from typing import Any

import httpx

from paisapal.providers.base import EvidenceSnapshot, redact_url_secrets

BASE_URL = "https://data.sec.gov"
TICKER_URL = "https://www.sec.gov/files/company_tickers.json"


class SecEdgarProvider:
    name = "sec_edgar"

    def __init__(
        self,
        http_client: Any | None = None,
        user_agent: str | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.http_client = http_client or httpx
        self.user_agent = user_agent or os.getenv(
            "SEC_USER_AGENT",
            "PaisaPal local app contact@example.com",
        )
        self.timeout = timeout

    def collect(self, ticker: str) -> list[EvidenceSnapshot]:
        try:
            company = self._company_for_ticker(ticker)
            if company is None:
                return [self._error_snapshot(ticker, "SEC ticker mapping did not include ticker")]
            cik = f"{int(company['cik_str']):010d}"
            facts = self._companyfacts(cik)
        except Exception as exc:
            return [self._error_snapshot(ticker, str(exc))]

        revenue = _latest_fact(facts, "Revenues")
        net_income = _latest_fact(facts, "NetIncomeLoss")
        assets = _latest_fact(facts, "Assets")
        liabilities = _latest_fact(facts, "Liabilities")
        equity = _latest_fact(facts, "StockholdersEquity")
        operating_cash_flow = _latest_fact(facts, "OperatingCashFlow")
        if operating_cash_flow is None:
            operating_cash_flow = _latest_fact(facts, "NetCashProvidedByUsedInOperatingActivities")

        return [
            EvidenceSnapshot(
                provider=self.name,
                source_type="fundamentals",
                status="fresh",
                label="SEC EDGAR company facts",
                payload={
                    "ticker": ticker.upper(),
                    "name": company.get("title"),
                    "cik": cik,
                },
                url=f"{BASE_URL}/api/xbrl/companyfacts/CIK{cik}.json",
            ),
            EvidenceSnapshot(
                provider=self.name,
                source_type="financials",
                status="fresh",
                label="SEC EDGAR financial statement facts",
                payload={
                    "ticker": ticker.upper(),
                    "income_statement": {
                        "revenue": revenue,
                        "net_income": net_income,
                    },
                    "balance_sheet": {
                        "assets": assets,
                        "liabilities": liabilities,
                        "stockholders_equity": equity,
                    },
                    "cash_flow": {
                        "operating_cash_flow": operating_cash_flow,
                    },
                },
                url=f"{BASE_URL}/api/xbrl/companyfacts/CIK{cik}.json",
            ),
            EvidenceSnapshot(
                provider=self.name,
                source_type="ratios",
                status="fresh",
                label="SEC EDGAR derived ratios",
                payload={
                    "ticker": ticker.upper(),
                    "net_margin": _ratio(net_income, revenue),
                    "debt_to_assets": _ratio(liabilities, assets),
                    "return_on_assets": _ratio(net_income, assets),
                    "return_on_equity": _ratio(net_income, equity),
                },
                url=f"{BASE_URL}/api/xbrl/companyfacts/CIK{cik}.json",
            ),
        ]

    def _company_for_ticker(self, ticker: str) -> dict[str, Any] | None:
        response = self.http_client.get(
            TICKER_URL,
            headers={"User-Agent": self.user_agent},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Unexpected SEC ticker mapping response")
        normalized = ticker.upper()
        for item in payload.values():
            if isinstance(item, dict) and str(item.get("ticker", "")).upper() == normalized:
                return item
        return None

    def _companyfacts(self, cik: str) -> dict[str, Any]:
        response = self.http_client.get(
            f"{BASE_URL}/api/xbrl/companyfacts/CIK{cik}.json",
            headers={"User-Agent": self.user_agent},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Unexpected SEC CompanyFacts response")
        return payload

    def _error_snapshot(self, ticker: str, warning: str) -> EvidenceSnapshot:
        return EvidenceSnapshot(
            provider=self.name,
            source_type="provider_status",
            status="error",
            label="SEC EDGAR CompanyFacts",
            payload={"ticker": ticker.upper()},
            url=TICKER_URL,
            warnings=[redact_url_secrets(warning)],
        )


def _latest_fact(payload: dict[str, Any], tag: str) -> int | float | None:
    facts = payload.get("facts", {}).get("us-gaap", {}).get(tag, {})
    units = facts.get("units", {}) if isinstance(facts, dict) else {}
    candidates = []
    for values in units.values():
        if not isinstance(values, list):
            continue
        candidates.extend(
            item
            for item in values
            if isinstance(item, dict) and item.get("val") is not None and item.get("form") in {"10-K", "10-Q"}
        )
    if not candidates:
        return None
    latest = sorted(
        candidates,
        key=lambda item: (
            int(item.get("fy") or 0),
            str(item.get("fp") or ""),
            str(item.get("end") or ""),
        ),
    )[-1]
    return latest.get("val")


def _ratio(numerator: int | float | None, denominator: int | float | None) -> float | None:
    if numerator is None or denominator in {None, 0}:
        return None
    return round(float(numerator) / float(denominator), 4)
