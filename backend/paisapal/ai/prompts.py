from __future__ import annotations

import json

from paisapal.analysis_runs.models import AnalysisRunSettings
from paisapal.providers.base import EvidenceSnapshot


REPORT_SECTIONS = [
    "1. Current Stock Context",
    "2. VCP / Technical Pattern View",
    "3. Entry, Stop-Loss, and Target Zones",
    "4. SEPA-Style Position Sizing",
    "5. Earnings Review",
    "6. Fundamental Metrics",
    "7. Market Sentiment",
    "8. Options Flow / Implied Move",
    "9. Final View",
]


def build_framework_prompt(
    ticker: str,
    settings: AnalysisRunSettings,
    evidence: list[EvidenceSnapshot],
) -> str:
    evidence_payload = [
        {
            "provider": item.provider,
            "source_type": item.source_type,
            "status": item.status,
            "label": item.label,
            "payload": item.payload,
            "warnings": item.warnings,
            "retrieved_at": item.retrieved_at,
        }
        for item in evidence
    ]
    return "\n".join(
        [
            f"Run the PaisaPal investment framework for ticker {ticker}.",
            "Use the supplied evidence first. Use web research only for recent context and citations.",
            "Return structured JSON matching the AiReportOutput schema and include full Markdown.",
            "The Markdown report must use these sections:",
            json.dumps(REPORT_SECTIONS),
            "Final classification must be one of: Buy / Enter, Watchlist, Wait for Pullback, Avoid, Reduce, Exit.",
            f"User risk settings: {settings.model_dump_json()}",
            f"Evidence: {json.dumps(evidence_payload)}",
        ]
    )
