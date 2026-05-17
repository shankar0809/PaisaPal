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
    _enforce_source_backed_current_price(report, evidence)
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
    report["markdown_report"] = _render_markdown_report(report, missing_labels, warnings)
    return report


def _enforce_source_backed_current_price(report: dict, evidence: list[EvidenceSnapshot]) -> None:
    price = _source_backed_current_price(evidence)
    if price is None:
        return
    report["current_price"] = price
    _sanitize_price_based_fields(report, price)
    report["markdown_report"] = _replace_current_price(
        report.get("markdown_report", ""),
        price,
    )


def _source_backed_current_price(evidence: list[EvidenceSnapshot]) -> float | None:
    for item in evidence:
        if item.status != "fresh" or item.source_type != "market":
            continue
        payload = item.payload
        session = payload.get("session", {})
        if isinstance(session, dict):
            price = _float_or_none(session.get("price"))
            if price is not None:
                return round(price, 2)
        price = _float_or_none(payload.get("latest_close") or payload.get("price"))
        if price is not None:
            return round(price, 2)
    for item in evidence:
        if item.status != "fresh" or item.source_type != "technicals":
            continue
        price = _float_or_none(item.payload.get("latest_close"))
        if price is not None:
            return round(price, 2)
    return None


def _replace_current_price(markdown: str, price: float) -> str:
    if not markdown:
        return markdown
    replacement = f"Current Price: ${price:.2f}"
    replaced = re.sub(
        r"(?im)(current\s+price\s*[:\-]\s*)\$?[\d,]+(?:\.\d+)?",
        replacement,
        markdown,
    )
    return replaced


def _sanitize_price_based_fields(report: dict, price: float) -> None:
    report["entry_zones"] = [f"${price:.2f}"]
    report["stop_zones"] = [f"${round(price * 0.95, 2):.2f}"]
    report["target_zones"] = [
        f"${round(price * 1.05, 2):.2f}",
        f"${round(price * 1.10, 2):.2f}",
    ]
    report["position_sizing"] = []


def _float_or_none(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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


def _render_markdown_report(report: dict, missing_labels: list[str], warnings: list[str]) -> str:
    markdown = [
        f"# {report.get('company_name', report.get('ticker', 'Unknown'))} ({report.get('ticker', 'Unknown')}) - Stock Analysis Report",
        "",
        "## Current Stock Context",
        f"- Current Price: ${_format_price(report.get('current_price'))}",
        f"- Confidence: {report.get('confidence', 'Unknown')}",
        f"- Final View: {report.get('final_classification') or report.get('final_decision') or 'Unknown'}",
        "",
        "## VCP / Technical Pattern View",
        f"- Technical Rating: {report.get('technical_rating', 'Missing')}",
        f"- VCP Rating: {report.get('vcp_rating', 'Missing')}",
        "",
        "## Entry, Stop-Loss, and Target Zones",
        f"- Entry Zones: {', '.join(report.get('entry_zones') or ['None'])}",
        f"- Stop Zones: {', '.join(report.get('stop_zones') or ['None'])}",
        f"- Target Zones: {', '.join(report.get('target_zones') or ['None'])}",
        "",
        "## SEPA-Style Position Sizing",
    ]
    position_sizing = report.get("position_sizing") or []
    if position_sizing:
        for scenario in position_sizing:
            markdown.append(
                "- "
                + ", ".join(
                    [
                        f"{scenario.get('label', 'Scenario')}",
                        f"entry ${_format_price(scenario.get('entry'))}",
                        f"stop ${_format_price(scenario.get('stop'))}",
                        f"risk/share ${_format_price(scenario.get('risk_per_share'))}",
                        f"shares {scenario.get('shares_at_max_risk', 0)}",
                    ]
                )
            )
    else:
        markdown.append("- None")
    markdown.extend(
        [
            "",
            "## Earnings Review",
            f"- Earnings Rating: {report.get('earnings_rating', 'Missing')}",
            "",
            "## Fundamental Metrics",
            f"- Fundamental Rating: {report.get('fundamental_rating', 'Missing')}",
            "",
            "## Market Sentiment",
            f"- Sentiment Rating: {report.get('sentiment_rating', 'Missing')}",
            "",
            "## Options Flow / Implied Move",
            f"- Options Flow Rating: {report.get('options_flow_rating', 'Missing')}",
            "",
            "## Final View",
            f"- Final Classification: {report.get('final_classification') or report.get('final_decision') or 'Unknown'}",
            f"- Risk/Reward: {report.get('risk_reward') if report.get('risk_reward') is not None else 'N/A'}",
        ]
    )
    if missing_labels or warnings:
        markdown.extend(["", "## Data Warnings"])
        markdown.extend(f"- {label}" for label in missing_labels)
        markdown.extend(f"- {warning}" for warning in warnings)
    analysis_steps = report.get("analysis_steps") or []
    if analysis_steps:
        markdown.append("")
        markdown.append("## Analysis Step Results")
        for step in analysis_steps:
            markdown.append(f"### {step.get('section', 'Step')}")
            markdown.append(f"- Status: {step.get('status', 'missing')}")
            markdown.append(f"- Summary: {step.get('summary', 'N/A')}")
            results = step.get("results") or {}
            if isinstance(results, dict) and results:
                markdown.append("- Results:")
                for key, value in results.items():
                    markdown.append(f"  - {key}: {value}")
            sources = step.get("sources") or []
            if sources:
                markdown.append("- Sources:")
                for source in sources:
                    markdown.append(
                        "  - "
                        + ", ".join(
                            [
                                str(source.get("provider", "unknown")),
                                str(source.get("label", "unknown")),
                                str(source.get("status", "unknown")),
                            ]
                        )
                    )
            step_warnings = step.get("warnings") or []
            if step_warnings:
                markdown.append("- Warnings:")
                markdown.extend(f"  - {warning}" for warning in step_warnings)
    return "\n".join(markdown)


def _format_price(value) -> str:
    price = _float_or_none(value)
    return f"{price:.2f}" if price is not None else "N/A"
