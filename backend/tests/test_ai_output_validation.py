import pytest
from pydantic import ValidationError

from paisapal.ai.evidence_map import build_framework_evidence_map
from paisapal.ai.prompts import build_framework_prompt
from paisapal.ai.schemas import validate_ai_report
from paisapal.analysis_runs.vcp_summary import build_vcp_summary_from_report
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

    assert "Framework section expectations:" in prompt
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
    assert by_section["VCP / Technical Pattern View"]["results"]["ticker"] == "NVDA"
    assert by_section["VCP / Technical Pattern View"]["results"]["vcp_score"] == 5
    assert by_section["VCP / Technical Pattern View"]["results"]["vcp_stage"] == "Stage 3"
    assert by_section["VCP / Technical Pattern View"]["results"]["tech_output"] == "VCP watchlist candidate"
    assert by_section["VCP / Technical Pattern View"]["results"]["vcp_rating"] == "Watchlist candidate"
    assert {source["provider"] for source in by_section["Current Stock Context"]["sources"]} >= {
        "yahoo",
        "sec_edgar",
    }


def test_build_vcp_summary_from_report_scores_rich_contraction_patterns():
    bars = []
    for day in range(40):
        if day < 20:
            close = 70 + day * 0.8
            volume = 100000 + day * 1000
            high = close + 4
            low = close - 4
        else:
            close = 90 + (day - 20) * 0.25
            volume = 60000 + (day - 20) * 500
            high = close + 2
            low = close - 2
        bars.append({"close": close, "high": high, "low": low, "volume": volume})

    report = {
        "ticker": "MSFT",
        "current_price": 95,
        "vcp_rating": "Positive",
        "technical_rating": "Strong Buy",
    }
    evidence = [
        EvidenceSnapshot(
            provider="yahoo",
            source_type="technicals",
            status="fresh",
            label="Yahoo Finance daily bars",
            payload={
                "ticker": "MSFT",
                "latest_close": 95,
                "sma_20": 94,
                "sma_50": 90,
                "range_high": 98,
                "range_low": 68,
                "bars": bars,
            },
        )
    ]

    summary = build_vcp_summary_from_report(report, evidence)

    assert summary["vcp_score"] >= 7.5
    assert summary["vcp_stage"] == "Stage 2"
    assert summary["tech_output"] == "Strong VCP watchlist candidate"


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


def test_enforce_missing_evidence_ratings_aligns_recovery_setups():
    report = valid_report()
    report["final_classification"] = "Buy / Enter"
    report["confidence"] = "High"
    report["technical_rating"] = "Strong Buy"
    report["vcp_rating"] = "Positive"
    report["options_flow_rating"] = "Missing"
    report["bullish_factors"] = ["Strong revenue growth"]
    report["bearish_risks"] = ["Intense competition in the industry"]
    evidence = [
        EvidenceSnapshot(
            provider="yahoo",
            source_type="market",
            status="fresh",
            label="Yahoo Finance chart quote",
            payload={"ticker": "CRM", "session": {"price": 173.51}},
        ),
        EvidenceSnapshot(
            provider="yahoo",
            source_type="technicals",
            status="fresh",
            label="Yahoo Finance daily bars",
            payload={
                "ticker": "CRM",
                "latest_close": 173.51,
                "sma_20": 179.763,
                "sma_50": 183.8232,
                "range_high": 269.11,
                "range_low": 163.52,
            },
        ),
    ]

    guarded = enforce_missing_evidence_ratings(report, evidence)

    assert guarded["final_classification"] == "Watchlist"
    assert guarded["confidence"] == "Medium"
    assert guarded["technical_rating"] == "Recovery / base-building"
    assert guarded["vcp_rating"] == "Watchlist candidate"
    assert guarded["entry_zones"] == [
        "Break and hold above $185-190",
        "Pullback to $167-$170",
    ]
    assert guarded["stop_zones"] == ["Below $160"]
    assert guarded["target_zones"] == ["$200-$205", "$220-$230"]
    assert guarded["bullish_factors"][0] == "Strong earnings and cash flow support a recovery setup"
    assert "## Final View" in guarded["markdown_report"]


def test_enforce_missing_evidence_ratings_keeps_breakouts_actionable():
    report = valid_report()
    report["final_classification"] = "Watchlist"
    report["confidence"] = "Medium"
    report["technical_rating"] = "Constructive"
    report["vcp_rating"] = "Watchlist candidate"
    report["options_flow_rating"] = "Bullish leaning"
    report["bullish_factors"] = ["Strong revenue growth"]
    report["bearish_risks"] = ["Crowded expectations"]
    evidence = [
        EvidenceSnapshot(
            provider="yahoo",
            source_type="market",
            status="fresh",
            label="Yahoo Finance chart quote",
            payload={"ticker": "ABC", "session": {"price": 205.0}},
        ),
        EvidenceSnapshot(
            provider="yahoo",
            source_type="technicals",
            status="fresh",
            label="Yahoo Finance daily bars",
            payload={
                "ticker": "ABC",
                "latest_close": 205.0,
                "sma_20": 198.0,
                "sma_50": 196.0,
                "range_high": 204.5,
                "range_low": 160.0,
            },
        ),
    ]

    guarded = enforce_missing_evidence_ratings(report, evidence)

    assert guarded["final_classification"] == "Buy / Enter"
    assert guarded["confidence"] == "High"
    assert guarded["technical_rating"] == "Breakout / trending"
    assert guarded["vcp_rating"] == "High-quality VCP"
    assert guarded["entry_zones"] == ["Break and hold above $200-205"]
    assert guarded["stop_zones"] == ["Below $190"]
    assert guarded["target_zones"] == ["$220-$225", "$240-$250"]
    assert guarded["bullish_factors"][0] == "Price is confirming above key moving averages and pivot resistance"
