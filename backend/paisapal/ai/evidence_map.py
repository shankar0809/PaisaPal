from __future__ import annotations

from paisapal.providers.base import EvidenceSnapshot

FRAMEWORK_SECTION_SOURCE_TYPES = {
    "1. Current Stock Context": {"market", "fundamentals"},
    "2. VCP / Technical Pattern View": {"market", "technicals"},
    "3. Entry, Stop-Loss, and Target Zones": {"market", "technicals"},
    "4. SEPA-Style Position Sizing": {"market", "technicals"},
    "5. Earnings Review": {"earnings"},
    "6. Fundamental Metrics": {"fundamentals", "financials", "ratios"},
    "7. Market Sentiment": {"news_sentiment"},
    "8. Options Flow / Implied Move": {"options"},
    "9. Final View": {
        "market",
        "technicals",
        "fundamentals",
        "financials",
        "ratios",
        "earnings",
        "news_sentiment",
        "options",
    },
}


def build_framework_evidence_map(evidence: list[EvidenceSnapshot]) -> list[dict]:
    provider_warnings = [
        {
            "provider": item.provider,
            "source_type": item.source_type,
            "status": item.status,
            "label": item.label,
            "warnings": item.warnings,
            "retrieved_at": item.retrieved_at,
        }
        for item in evidence
        if item.status in {"missing", "error"} or item.warnings
    ]
    return [
        {
            "section": section,
            "expected_source_types": sorted(source_types),
            "sources": [_source_ref(item) for item in evidence if item.source_type in source_types],
            "provider_warnings": provider_warnings if section == "9. Final View" else [],
        }
        for section, source_types in FRAMEWORK_SECTION_SOURCE_TYPES.items()
    ]


def _source_ref(item: EvidenceSnapshot) -> dict:
    return {
        "provider": item.provider,
        "source_type": item.source_type,
        "status": item.status,
        "label": item.label,
        "url": item.url,
        "warnings": item.warnings,
        "retrieved_at": item.retrieved_at,
    }
