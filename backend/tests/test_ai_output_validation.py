import pytest
from pydantic import ValidationError

from paisapal.ai.evidence_map import build_framework_evidence_map
from paisapal.ai.prompts import build_framework_prompt
from paisapal.ai.schemas import validate_ai_report
from paisapal.analysis_runs.evidence_guard import enforce_missing_evidence_ratings
from paisapal.analysis_runs.source_coverage import derive_source_coverage
from paisapal.analysis_runs.step_details import build_analysis_steps
from paisapal.analysis_runs.models import AnalysisRunSettings
from paisapal.providers.base import EvidenceSnapshot


def valid_report():
    return {
        "ticker": "NVDA",
        "company_name": "NVIDIA Corporation",
        "current_price": 211.5,
        "final_classification": "Watchlist",
        "confidence": "Medium",
        "technical_rating": "Constructive",
        "vcp_rating": "Watchlist candidate",
        "fundamental_rating": "Very strong",
        "earnings_rating": "Strong",
        "sentiment_rating": "Bullish but crowded",
        "options_flow_rating": "Call-heavy",
        "risk_reward": 2.1,
        "entry_zones": ["$217-$219"],
        "stop_zones": ["$208-$209"],
        "target_zones": ["$228-$230"],
        "position_sizing": [],
        "bullish_factors": ["AI data center leadership"],
        "bearish_risks": ["Crowded expectations"],
        "data_warnings": [],
        "source_summary": [],
        "markdown_report": "# NVIDIA Corporation (NVDA) - Stock Analysis Report",
    }


def test_validate_ai_report_accepts_allowed_classification():
    report = validate_ai_report(valid_report())
    assert report.final_classification == "Watchlist"


def test_validate_ai_report_rejects_unapproved_classification():
    payload = valid_report()
    payload["final_classification"] = "Strong Buy"

    with pytest.raises(ValidationError):
        validate_ai_report(payload)


def test_validate_ai_report_rejects_non_positive_current_price():
    payload = valid_report()
    payload["current_price"] = 0

    with pytest.raises(ValidationError):
        validate_ai_report(payload)


def test_build_framework_prompt_includes_evidence_urls():
    evidence = [
        EvidenceSnapshot(
            provider="example",
            source_type="news",
            status="fresh",
            label="Example source",
            payload={"headline": "NVIDIA expands data center revenue"},
            url="https://example.com/source",
            retrieved_at="2026-05-15T12:00:00+00:00",
        )
    ]

    prompt = build_framework_prompt(
        ticker="NVDA",
        settings=AnalysisRunSettings(),
        evidence=evidence,
    )

    assert "https://example.com/source" in prompt


def test_build_framework_evidence_map_groups_sources_by_framework_section():
    evidence = [
        EvidenceSnapshot(provider="polygon", source_type="technicals", status="fresh", label="Daily bars", payload={}),
        EvidenceSnapshot(provider="polygon", source_type="options", status="fresh", label="Options chain", payload={}),
        EvidenceSnapshot(provider="fmp", source_type="ratios", status="fresh", label="Ratios", payload={}),
        EvidenceSnapshot(provider="alpha_vantage", source_type="news_sentiment", status="fresh", label="News", payload={}),
        EvidenceSnapshot(
            provider="alpha_vantage",
            source_type="provider_status",
            status="error",
            label="Rate limit",
            payload={},
            warnings=["rate limited"],
        ),
    ]

    evidence_map = build_framework_evidence_map(evidence)

    by_section = {section["section"]: section for section in evidence_map}
    assert by_section["2. VCP / Technical Pattern View"]["sources"][0]["source_type"] == "technicals"
    assert by_section["6. Fundamental Metrics"]["sources"][0]["source_type"] == "ratios"
    assert by_section["7. Market Sentiment"]["sources"][0]["source_type"] == "news_sentiment"
    assert by_section["8. Options Flow / Implied Move"]["sources"][0]["source_type"] == "options"
    assert by_section["9. Final View"]["provider_warnings"][0]["warnings"] == ["rate limited"]


def test_build_framework_prompt_includes_framework_evidence_map_and_quality_rules():
    evidence = [
        EvidenceSnapshot(
            provider="polygon",
            source_type="technicals",
            status="fresh",
            label="Daily bars",
            payload={"latest_close": 130},
        )
    ]

    prompt = build_framework_prompt(
        ticker="NVDA",
        settings=AnalysisRunSettings(),
        evidence=evidence,
    )

    assert "Framework evidence map:" in prompt
    assert "2. VCP / Technical Pattern View" in prompt
    assert "Use source-backed commentary in every framework section" in prompt
    assert "If evidence is missing or weak, say so explicitly" in prompt


def test_build_framework_prompt_compacts_large_evidence_payloads():
    evidence = [
        EvidenceSnapshot(
            provider="fred",
            source_type="macro",
            status="fresh",
            label="FRED macro series FEDFUNDS",
            payload={
                "series_id": "FEDFUNDS",
                "observations": [{"date": f"2026-05-{day:02d}", "value": day} for day in range(1, 51)],
                "notes": "x" * 2000,
            },
        )
    ]

    prompt = build_framework_prompt(
        ticker="NVDA",
        settings=AnalysisRunSettings(),
        evidence=evidence,
    )

    assert "\"date\": \"2026-05-50\"" not in prompt
    assert len(prompt) < 12000


def test_derive_source_coverage_counts_unique_source_types_and_keeps_covered_sections_clean():
    report = {
        "source_summary": [
            {"provider": "yahoo", "source_type": "market", "status": "fresh", "label": "Yahoo quote", "url": None, "warnings": []},
            {"provider": "polygon", "source_type": "market", "status": "fresh", "label": "Polygon snapshot", "url": None, "warnings": []},
            {"provider": "sec_edgar", "source_type": "fundamentals", "status": "fresh", "label": "SEC facts", "url": None, "warnings": []},
            {"provider": "finnhub", "source_type": "options", "status": "missing", "label": "Finnhub option-chain", "url": None, "warnings": ["Forbidden"]},
        ]
    }

    coverage = derive_source_coverage(report)
    by_section = {item["section"]: item for item in coverage}

    assert by_section["Current Stock Context"]["status"] == "covered"
    assert by_section["Current Stock Context"]["warnings"] == []
    assert by_section["Final View"]["status"] == "partial"
    assert by_section["Final View"]["warnings"] == ["Forbidden"]
    assert "Forbidden" in by_section["Options Flow / Implied Move"]["warnings"]


def test_build_analysis_steps_includes_section_results_and_sources():
    report = valid_report()
    report["analysis_steps"] = []
    evidence = [
        EvidenceSnapshot(
            provider="yahoo",
            source_type="market",
            status="fresh",
            label="Yahoo Finance chart quote",
            payload={"session": {"price": 225.32}},
        ),
        EvidenceSnapshot(
            provider="sec_edgar",
            source_type="fundamentals",
            status="fresh",
            label="SEC facts",
            payload={},
        ),
        EvidenceSnapshot(
            provider="polygon",
            source_type="technicals",
            status="fresh",
            label="Polygon daily bars",
            payload={"latest_close": 225.32},
        ),
    ]

    steps = build_analysis_steps(report, evidence)
    by_section = {item["section"]: item for item in steps}

    assert by_section["Current Stock Context"]["status"] == "covered"
    assert by_section["Current Stock Context"]["results"]["current_price"] == "211.50"
    assert by_section["VCP / Technical Pattern View"]["results"]["technical_rating"] == "Constructive"
    assert {source["provider"] for source in by_section["Current Stock Context"]["sources"]} >= {
        "yahoo",
        "sec_edgar",
    }


def test_enforce_missing_evidence_ratings_overrides_unsupported_ai_claims():
    report = valid_report()
    report["markdown_report"] = "\n".join(
        [
            "# NVIDIA Corporation (NVDA) - Stock Analysis Report",
            "- **Earnings Rating:** Strong",
            "- **Sentiment Rating:** Bullish",
            "- **Options Flow Rating:** Call-heavy",
        ]
    )
    report["bullish_factors"] = [
        "Strong revenue growth",
        "Positive earnings outlook",
        "Bullish options flow",
        "Improving sentiment",
    ]
    evidence = [
        EvidenceSnapshot(
            provider="sec_edgar",
            source_type="fundamentals",
            status="fresh",
            label="SEC facts",
            payload={},
        )
    ]

    guarded = enforce_missing_evidence_ratings(report, evidence)

    assert guarded["technical_rating"] == "Missing"
    assert guarded["vcp_rating"] == "Missing"
    assert guarded["earnings_rating"] == "Missing"
    assert guarded["sentiment_rating"] == "Missing"
    assert guarded["options_flow_rating"] == "Missing"
    assert "Missing options flow evidence" in guarded["data_warnings"]
    assert "## Earnings Review" in guarded["markdown_report"]
    assert "- Earnings Rating: Missing" in guarded["markdown_report"]
    assert "## Market Sentiment" in guarded["markdown_report"]
    assert "- Sentiment Rating: Missing" in guarded["markdown_report"]
    assert "## Options Flow / Implied Move" in guarded["markdown_report"]
    assert "- Options Flow Rating: Missing" in guarded["markdown_report"]
    assert "## Data Warnings" in guarded["markdown_report"]
    assert guarded["bullish_factors"] == ["Strong revenue growth"]


def test_enforce_missing_evidence_ratings_overrides_ai_current_price_with_market_evidence():
    report = valid_report()
    report["current_price"] = 320.5
    report["markdown_report"] = "\n".join(
        [
            "# NVIDIA Corporation (NVDA) - Stock Analysis Report",
            "- Current Price: $320.50",
        ]
    )
    evidence = [
        EvidenceSnapshot(
            provider="yahoo",
            source_type="market",
            status="fresh",
            label="Yahoo Finance chart quote",
            payload={
                "ticker": "NVDA",
                "session": {"price": 225.32},
            },
        ),
        EvidenceSnapshot(
            provider="yahoo",
            source_type="technicals",
            status="fresh",
            label="Yahoo Finance daily bars",
            payload={"latest_close": 225.32000732421875},
        ),
    ]

    guarded = enforce_missing_evidence_ratings(report, evidence)

    assert guarded["current_price"] == 225.32
    assert "Current Price: $225.32" in guarded["markdown_report"]


def test_enforce_missing_evidence_ratings_rewrites_stale_trade_plan_prices():
    report = valid_report()
    report["current_price"] = 320.5
    report["entry_zones"] = ["$310-$320.50"]
    report["stop_zones"] = ["$310.00"]
    report["target_zones"] = ["$340-$360"]
    report["position_sizing"] = [
        {
            "label": "Initial Position",
            "entry": 320.5,
            "stop": 310.0,
            "risk_per_share": 10.5,
            "shares_at_max_risk": 10,
        }
    ]
    evidence = [
        EvidenceSnapshot(
            provider="yahoo",
            source_type="market",
            status="fresh",
            label="Yahoo Finance chart quote",
            payload={"ticker": "NVDA", "session": {"price": 225.32}},
        ),
        EvidenceSnapshot(
            provider="yahoo",
            source_type="technicals",
            status="fresh",
            label="Yahoo Finance daily bars",
            payload={"latest_close": 225.32000732421875},
        ),
    ]

    guarded = enforce_missing_evidence_ratings(report, evidence)

    assert guarded["current_price"] == 225.32
    assert guarded["entry_zones"] == ["$225.32"]
    assert guarded["stop_zones"] == ["$214.05"]
    assert guarded["target_zones"] == ["$236.59", "$247.85"]
    assert guarded["position_sizing"] == []
    assert "Current Price: $225.32" in guarded["markdown_report"]
    assert "## Current Stock Context" in guarded["markdown_report"]
