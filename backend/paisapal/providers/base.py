from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class EvidenceSnapshot:
    provider: str
    source_type: str
    status: str
    label: str
    payload: dict
    url: str | None = None
    warnings: list[str] = field(default_factory=list)
    retrieved_at: str = field(default_factory=utc_iso)

    def as_source_row(self) -> dict:
        return {
            "provider": self.provider,
            "source_type": self.source_type,
            "status": self.status,
            "label": self.label,
            "url": self.url,
            "payload": self.payload,
            "warnings": self.warnings,
            "retrieved_at": self.retrieved_at,
        }


class MarketDataProvider(Protocol):
    name: str

    def collect(self, ticker: str) -> list[EvidenceSnapshot]:
        """Return normalized evidence snapshots for one ticker."""
