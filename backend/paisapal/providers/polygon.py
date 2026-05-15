from __future__ import annotations

import os

from paisapal.providers.base import EvidenceSnapshot


class PolygonProvider:
    name = "polygon"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("POLYGON_API_KEY")

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
        return [
            EvidenceSnapshot(
                provider=self.name,
                source_type="provider_status",
                status="fresh",
                label="Polygon configured",
                payload={"ticker": ticker},
            )
        ]
