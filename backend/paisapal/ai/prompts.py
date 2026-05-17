from __future__ import annotations

import json

from paisapal.ai.evidence_map import build_framework_evidence_map
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
            "url": item.url,
            "payload": _compact_value(item.payload),
            "warnings": item.warnings,
            "retrieved_at": item.retrieved_at,
        }
        for item in evidence
    ]
    framework_evidence_map = build_framework_evidence_map(evidence)
    return "\n".join(
        [
            f"Run the PaisaPal investment framework for ticker {ticker}.",
            "Use the supplied evidence first. Use web research only for recent context and citations.",
            "Return valid JSON matching the AiReportOutput schema and include full Markdown.",
            "Use source-backed commentary in every framework section.",
            "If evidence is missing or weak, say so explicitly in the relevant section and data_warnings.",
            "Do not invent confidence, options flow, earnings strength, or technical signals when source evidence is missing.",
            "The Markdown report must use these sections:",
            json.dumps(REPORT_SECTIONS),
            "Final classification must be one of: Buy / Enter, Watchlist, Wait for Pullback, Avoid, Reduce, Exit.",
            f"User risk settings: {settings.model_dump_json()}",
            f"Framework evidence map: {json.dumps(framework_evidence_map)}",
            f"Evidence: {json.dumps(evidence_payload)}",
        ]
    )


def _compact_value(value, depth: int = 0):
    if depth >= 2:
        if isinstance(value, str):
            return value[:240]
        return value
    if isinstance(value, dict):
        compacted = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= 8:
                compacted["_truncated_keys"] = len(value) - 8
                break
            compacted[key] = _compact_value(item, depth + 1)
        return compacted
    if isinstance(value, list):
        compacted_list = [_compact_value(item, depth + 1) for item in value[:3]]
        if len(value) > 3:
            compacted_list.append({"_truncated_items": len(value) - 3})
        return compacted_list
    if isinstance(value, str):
        return value[:240]
    return value
