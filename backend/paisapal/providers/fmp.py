from __future__ import annotations

import os

from paisapal.providers.base import EvidenceSnapshot


class FmpProvider:
    name = "fmp"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("FMP_API_KEY")

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
        return [
            EvidenceSnapshot(
                provider=self.name,
                source_type="provider_status",
                status="fresh",
                label="Financial Modeling Prep configured",
                payload={"ticker": ticker},
            )
        ]
