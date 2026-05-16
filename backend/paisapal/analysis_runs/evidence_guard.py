from __future__ import annotations

import re

from paisapal.providers.base import EvidenceSnapshot

_FIELD_REQUIREMENTS = {
    "technical_rating": ({"technicals", "market"}, "Technical Rating", "Missing technical evidence"),
    "vcp_rating": ({"technicals", "market"}, "VCP Rating", "Missing technical evidence"),
    "earnings_rating": ({"earnings"}, "Earnings Rating", "Missing earnings evidence"),
    "sentiment_rating": ({"news_sentiment"}, "Sentiment Rating", "Missing market sentiment evidence"),
    "options_flow_rating": ({"options"}, "Options Flow Rating", "Missing options flow evidence"),
}


def enforce_missing_evidence_ratings(report: dict, evidence: list[EvidenceSnapshot]) -> dict:
    fresh_source_types = {item.source_type for item in evidence if item.status == "fresh"}
    warnings = list(report.get("data_warnings") or [])
    missing_labels = []
    for field, (required_source_types, label, warning) in _FIELD_REQUIREMENTS.items():
        if fresh_source_types & required_source_types:
            continue
        report[field] = "Missing"
        missing_labels.append(label)
        _filter_factor_claims(report, required_source_types)
        if warning not in warnings:
            warnings.append(warning)
    report["data_warnings"] = warnings
    report["markdown_report"] = _guard_markdown(report.get("markdown_report", ""), missing_labels, warnings)
    return report


def _filter_factor_claims(report: dict, missing_source_types: set[str]) -> None:
    keywords = []
    if "earnings" in missing_source_types:
        keywords.extend(["earnings", "eps"])
    if "news_sentiment" in missing_source_types:
        keywords.extend(["sentiment", "news"])
    if "options" in missing_source_types:
        keywords.extend(["options", "flow", "implied"])
    if not keywords:
        return
    for field in ("bullish_factors", "bearish_risks"):
        values = report.get(field)
        if not isinstance(values, list):
            continue
        report[field] = [
            value
            for value in values
            if not any(keyword in str(value).lower() for keyword in keywords)
        ]


def _guard_markdown(markdown: str, missing_labels: list[str], warnings: list[str]) -> str:
    guarded = markdown
    for label in missing_labels:
        guarded = re.sub(
            rf"(?im)^(\s*[-*]?\s*\*\*{re.escape(label)}:\*\*)\s*.*$",
            r"\1 Missing",
            guarded,
        )
    if warnings:
        warning_block = "\n".join(f"- {warning}" for warning in warnings)
        guarded = f"{guarded.rstrip()}\n\n## Data Warnings\n{warning_block}"
    return guarded
