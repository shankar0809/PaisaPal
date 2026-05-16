from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from typing import Protocol


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def redact_url_secrets(message: str) -> str:
    return re.sub(
        r"(?i)([?&](?:apikey|api_key|token)=)[^&'\"\s]+",
        r"\1[REDACTED]",
        message,
    )


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
