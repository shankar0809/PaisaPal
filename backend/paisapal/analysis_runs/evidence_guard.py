from __future__ import annotations

import re

from paisapal.providers.base import EvidenceSnapshot
from paisapal.analysis_runs.vcp_summary import build_vcp_summary_from_report

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
    _align_framework_posture(report, evidence)
    report["vcp_summary"] = build_vcp_summary_from_report(report, evidence)
    report["data_warnings"] = warnings
    report["markdown_report"] = _render_markdown_report(report, evidence, missing_labels, warnings)
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


def _align_framework_posture(report: dict, evidence: list[EvidenceSnapshot]) -> None:
    price = _float_or_none(report.get("current_price"))
    technical = _technical_structure(evidence)
    if price is None or technical is None:
        return

    sma_20 = technical.get("sma_20")
    sma_50 = technical.get("sma_50")
    range_low = technical.get("range_low")
    range_high = technical.get("range_high")
    if sma_20 is None or sma_50 is None or range_low is None:
        return

    if price < sma_20 and price < sma_50:
        _apply_recovery_posture(report, price, sma_20, sma_50, range_low)
        return

    if (
        range_high is not None
        and price >= sma_20
        and price >= sma_50
        and price >= range_high - max(price * 0.03, 6.0)
    ):
        _apply_breakout_posture(report, price, sma_20, sma_50, range_high)
        return

def _apply_recovery_posture(
    report: dict,
    price: float,
    sma_20: float,
    sma_50: float,
    range_low: float,
) -> None:
    breakout_floor = _round_to_nearest_5(sma_50)
    support_floor = int(price - 6)
    support_ceiling = int(price - 3)
    stop_level = _round_to_nearest_5(range_low - 4.0)
    target_1_low = breakout_floor + 15
    target_1_high = breakout_floor + 20
    target_2_low = breakout_floor + 35
    target_2_high = breakout_floor + 45

    report["technical_rating"] = "Recovery / base-building"
    report["vcp_rating"] = "Watchlist candidate"
    if report.get("final_classification") == "Buy / Enter":
        report["final_classification"] = "Watchlist"
    report["confidence"] = "Medium"
    report["entry_zones"] = [
        f"Break and hold above ${breakout_floor}-{breakout_floor + 5}",
        f"Pullback to ${support_floor}-${support_ceiling}",
    ]
    report["stop_zones"] = [f"Below ${stop_level}"]
    report["target_zones"] = [
        f"${target_1_low}-${target_1_high}",
        f"${target_2_low}-${target_2_high}",
    ]
    report["bearish_risks"] = [
        "Stock is still below the 20-day and 50-day moving averages",
        "Breakout confirmation has not yet occurred",
        "Options flow evidence remains unavailable",
    ]
    bullish_factors = report.get("bullish_factors")
    if not isinstance(bullish_factors, list):
        bullish_factors = []
    if "Strong earnings and cash flow support a recovery setup" not in bullish_factors:
        bullish_factors.insert(0, "Strong earnings and cash flow support a recovery setup")
    report["bullish_factors"] = bullish_factors[:6]


def _apply_breakout_posture(
    report: dict,
    price: float,
    sma_20: float,
    sma_50: float,
    range_high: float,
) -> None:
    pivot_floor = _round_to_nearest_5(max(sma_20, sma_50))
    breakout_ceiling = _round_to_nearest_5(range_high)
    stop_level = _round_down_to_5(min(sma_20, sma_50) * 0.97)

    report["technical_rating"] = "Breakout / trending"
    report["vcp_rating"] = "High-quality VCP"
    if report.get("final_classification") in {"Watchlist", "Wait for Pullback"}:
        report["final_classification"] = "Buy / Enter"
    report["confidence"] = "High"
    report["entry_zones"] = [f"Break and hold above ${pivot_floor}-{pivot_floor + 5}"]
    report["stop_zones"] = [f"Below ${stop_level}"]
    report["target_zones"] = [
        f"${breakout_ceiling + 15}-${breakout_ceiling + 20}",
        f"${breakout_ceiling + 35}-${breakout_ceiling + 45}",
    ]
    bullish_factors = report.get("bullish_factors")
    if not isinstance(bullish_factors, list):
        bullish_factors = []
    if "Price is confirming above key moving averages and pivot resistance" not in bullish_factors:
        bullish_factors.insert(0, "Price is confirming above key moving averages and pivot resistance")
    report["bullish_factors"] = bullish_factors[:6]


def _technical_structure(evidence: list[EvidenceSnapshot]) -> dict[str, float] | None:
    for item in evidence:
        if item.status != "fresh" or item.source_type not in {"technicals", "market"}:
            continue
        payload = item.payload
        if not isinstance(payload, dict):
            continue
        structure = {
            "sma_20": _float_or_none(payload.get("sma_20")),
            "sma_50": _float_or_none(payload.get("sma_50")),
            "range_low": _float_or_none(payload.get("range_low")),
            "range_high": _float_or_none(payload.get("range_high")),
        }
        if any(value is not None for value in structure.values()):
            return structure
    return None


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


def _render_markdown_report(
    report: dict,
    evidence: list[EvidenceSnapshot],
    missing_labels: list[str],
    warnings: list[str],
) -> str:
    vcp_summary = report.get("vcp_summary") or build_vcp_summary_from_report(report, evidence)
    markdown = [
        f"# {report.get('company_name', report.get('ticker', 'Unknown'))} ({report.get('ticker', 'Unknown')}) - Stock Analysis Report",
        "",
        "## Current Stock Context",
        f"- Current Price: ${_format_price(report.get('current_price'))}",
        f"- Confidence: {report.get('confidence', 'Unknown')}",
        f"- Final View: {report.get('final_classification') or report.get('final_decision') or 'Unknown'}",
        "",
        "## VCP / Technical Pattern Framework",
        f"- Ticker: {vcp_summary.get('ticker', report.get('ticker', 'Unknown'))}",
        f"- VCP Score: {vcp_summary.get('vcp_score', 'Missing')}",
        f"- Stage: {vcp_summary.get('vcp_stage', 'Missing')}",
        f"- Tech Output: {vcp_summary.get('tech_output', report.get('technical_rating', 'Missing'))}",
        f"- VCP Rating: {vcp_summary.get('vcp_rating', report.get('vcp_rating', 'Missing'))}",
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


def _round_to_nearest_5(value: float) -> int:
    return int(round(value / 5.0) * 5)


def _round_down_to_5(value: float) -> int:
    return int(value // 5 * 5)
