from __future__ import annotations

SECTION_SOURCE_TYPES = {
    "Current Stock Context": {"market", "fundamentals"},
    "VCP / Technical Pattern View": {"market", "technicals"},
    "Entry, Stop-Loss, and Target Zones": {"market", "technicals"},
    "SEPA-Style Position Sizing": {"market", "technicals"},
    "Earnings Review": {"earnings"},
    "Fundamental Metrics": {"fundamentals", "financials", "ratios"},
    "Market Sentiment": {"news_sentiment"},
    "Options Flow / Implied Move": {"options"},
    "Final View": {
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

SOURCE_TYPE_LABEL_HINTS = {
    "market": ("market", "price", "snapshot", "daily"),
    "technicals": ("technical", "aggregate", "bar", "vcp"),
    "fundamentals": ("fundamental", "overview", "profile", "company"),
    "financials": ("financial", "statement", "cash flow", "balance"),
    "ratios": ("ratio", "score", "metric"),
    "earnings": ("earning", "eps"),
    "news_sentiment": ("news", "sentiment"),
    "options": ("option", "chain", "implied"),
}


def derive_source_coverage(report: dict) -> list[dict]:
    sources = report.get("source_summary", [])
    return [
        _coverage_row(section, source_types, sources)
        for section, source_types in SECTION_SOURCE_TYPES.items()
    ]


def _coverage_row(section: str, source_types: set[str], sources: list[dict]) -> dict:
    matched = [
        source
        for source in sources
        if _source_matches_types(source, source_types) and source.get("status") == "fresh"
    ]
    warning_sources = [
        source for source in sources if _source_matches_types(source, source_types) and source.get("warnings")
    ]
    if len(matched) >= len(source_types):
        status = "covered"
    elif matched:
        status = "partial"
    else:
        status = "missing"
    return {
        "section": section,
        "status": status,
        "matched_sources": [
            {
                "provider": source.get("provider"),
                "label": source.get("label"),
                "status": source.get("status"),
                "url": source.get("url"),
            }
            for source in matched
        ],
        "warnings": [
            warning
            for source in warning_sources
            for warning in source.get("warnings", [])
        ],
    }


def _source_matches_types(source: dict, source_types: set[str]) -> bool:
    source_type = source.get("source_type")
    if source_type in source_types:
        return True
    label = str(source.get("label", "")).lower()
    return any(
        hint in label
        for source_type in source_types
        for hint in SOURCE_TYPE_LABEL_HINTS.get(source_type, ())
    )
