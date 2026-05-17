from __future__ import annotations

from collections import defaultdict
from typing import Any

from paisapal.analysis_runs.source_coverage import SECTION_SOURCE_TYPES
from paisapal.analysis_runs.vcp_summary import build_vcp_summary_from_report
from paisapal.providers.base import EvidenceSnapshot


def build_analysis_steps(report: dict, evidence: list[EvidenceSnapshot]) -> list[dict[str, Any]]:
    grouped = _group_evidence_by_source_type(evidence)
    steps: list[dict[str, Any]] = []
    for section, source_types in SECTION_SOURCE_TYPES.items():
        matched = _matched_evidence(grouped, source_types)
        steps.append(
            {
                "section": section,
                "status": _step_status(matched, source_types),
                "summary": _summary_for_section(section, report),
                "results": _results_for_section(section, report),
                "sources": [
                    {
                        "provider": item.provider,
                        "source_type": item.source_type,
                        "status": item.status,
                        "label": item.label,
                    }
                    for item in matched
                ],
                "warnings": _unique_warnings(
                    warning for item in matched for warning in item.warnings if item.warnings
                ),
            }
        )
    return steps


def render_analysis_steps_markdown(steps: list[dict[str, Any]]) -> str:
    if not steps:
        return ""
    lines = ["## Analysis Step Results"]
    for step in steps:
        lines.extend(
            [
                "",
                f"### {step.get('section', 'Step')}",
                f"- Status: {step.get('status', 'missing')}",
                f"- Summary: {step.get('summary', 'N/A')}",
            ]
        )
        results = step.get("results") or {}
        if isinstance(results, dict) and results:
            lines.append("- Results:")
            for key, value in results.items():
                lines.append(f"  - {key}: {value}")
        sources = step.get("sources") or []
        if sources:
            lines.append("- Sources:")
            for source in sources:
                lines.append(
                    "  - "
                    + ", ".join(
                        [
                            str(source.get("provider", "unknown")),
                            str(source.get("label", "unknown")),
                            str(source.get("status", "unknown")),
                        ]
                    )
                )
        warnings = step.get("warnings") or []
        if warnings:
            lines.append("- Warnings:")
            for warning in warnings:
                lines.append(f"  - {warning}")
    return "\n".join(lines)


def _group_evidence_by_source_type(evidence: list[EvidenceSnapshot]) -> dict[str, list[EvidenceSnapshot]]:
    grouped: dict[str, list[EvidenceSnapshot]] = defaultdict(list)
    for item in evidence:
        grouped[item.source_type].append(item)
    return grouped


def _matched_evidence(
    grouped: dict[str, list[EvidenceSnapshot]],
    source_types: set[str],
) -> list[EvidenceSnapshot]:
    matched: list[EvidenceSnapshot] = []
    for source_type in source_types:
        matched.extend([item for item in grouped.get(source_type, []) if item.status == "fresh"])
    return matched


def _step_status(matched: list[EvidenceSnapshot], source_types: set[str]) -> str:
    matched_types = {item.source_type for item in matched}
    if matched_types >= source_types:
        return "covered"
    if matched_types:
        return "partial"
    return "missing"


def _summary_for_section(section: str, report: dict) -> str:
    if section == "Current Stock Context":
        return (
            f"Price ${_format_price(report.get('current_price'))}, "
            f"confidence {report.get('confidence', 'Unknown')}, "
            f"final view {report.get('final_classification') or report.get('final_decision') or 'Unknown'}."
        )
    if section == "VCP / Technical Pattern View":
        summary = _vcp_summary(report)
        return (
            f"{summary['ticker']} sits in {summary['vcp_stage']} with "
            f"score {summary['vcp_score']}, tech output {summary['tech_output']}, "
            f"and VCP rating {summary['vcp_rating']}."
        )
    if section == "Entry, Stop-Loss, and Target Zones":
        entry = ", ".join(report.get("entry_zones") or ["None"])
        stop = ", ".join(report.get("stop_zones") or ["None"])
        target = ", ".join(report.get("target_zones") or ["None"])
        return f"Entry {entry}; stop {stop}; targets {target}."
    if section == "SEPA-Style Position Sizing":
        sizing = report.get("position_sizing") or []
        return "Position sizing scenarios were generated." if sizing else "No position sizing scenarios were generated."
    if section == "Earnings Review":
        return f"Earnings rating {report.get('earnings_rating', 'Missing')}."
    if section == "Fundamental Metrics":
        return f"Fundamental rating {report.get('fundamental_rating', 'Missing')}."
    if section == "Market Sentiment":
        return f"Sentiment rating {report.get('sentiment_rating', 'Missing')}."
    if section == "Options Flow / Implied Move":
        return f"Options flow rating {report.get('options_flow_rating', 'Missing')}."
    return (
        f"Final classification {report.get('final_classification') or report.get('final_decision') or 'Unknown'} "
        f"with confidence {report.get('confidence', 'Unknown')}."
    )


def _results_for_section(section: str, report: dict) -> dict[str, Any]:
    if section == "Current Stock Context":
        return {
            "current_price": _format_price(report.get("current_price")),
            "confidence": report.get("confidence", "Unknown"),
            "final_classification": report.get("final_classification") or report.get("final_decision") or "Unknown",
        }
    if section == "VCP / Technical Pattern View":
        summary = _vcp_summary(report)
        return {
            "ticker": summary["ticker"],
            "vcp_score": summary["vcp_score"],
            "vcp_stage": summary["vcp_stage"],
            "tech_output": summary["tech_output"],
            "vcp_rating": summary["vcp_rating"],
        }
    if section == "Entry, Stop-Loss, and Target Zones":
        return {
            "entry_zones": ", ".join(report.get("entry_zones") or ["None"]),
            "stop_zones": ", ".join(report.get("stop_zones") or ["None"]),
            "target_zones": ", ".join(report.get("target_zones") or ["None"]),
            "risk_reward": "N/A" if report.get("risk_reward") is None else report.get("risk_reward"),
        }
    if section == "SEPA-Style Position Sizing":
        position_sizing = report.get("position_sizing") or []
        if not position_sizing:
            return {"position_sizing": "None"}
        return {
            "position_sizing": [
                {
                    "label": scenario.get("label"),
                    "entry": _format_price(scenario.get("entry")),
                    "stop": _format_price(scenario.get("stop")),
                    "risk_per_share": _format_price(scenario.get("risk_per_share")),
                    "shares_at_max_risk": scenario.get("shares_at_max_risk", 0),
                }
                for scenario in position_sizing
                if isinstance(scenario, dict)
            ]
        }
    if section == "Earnings Review":
        return {"earnings_rating": report.get("earnings_rating", "Missing")}
    if section == "Fundamental Metrics":
        return {"fundamental_rating": report.get("fundamental_rating", "Missing")}
    if section == "Market Sentiment":
        return {"sentiment_rating": report.get("sentiment_rating", "Missing")}
    if section == "Options Flow / Implied Move":
        return {"options_flow_rating": report.get("options_flow_rating", "Missing")}
    return {
        "final_classification": report.get("final_classification") or report.get("final_decision") or "Unknown",
        "confidence": report.get("confidence", "Unknown"),
        "data_warnings": ", ".join(report.get("data_warnings") or ["None"]),
    }


def _unique_warnings(warnings: Any) -> list[str]:
    if not isinstance(warnings, list):
        return []
    seen = set()
    deduped: list[str] = []
    for warning in warnings:
        if warning in seen:
            continue
        seen.add(warning)
        deduped.append(warning)
    return deduped


def _format_price(value: Any) -> str:
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return "N/A"


def _vcp_summary(report: dict) -> dict[str, Any]:
    summary = report.get("vcp_summary")
    if isinstance(summary, dict):
        return summary
    return build_vcp_summary_from_report(report)
