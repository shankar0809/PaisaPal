import pytest
from pydantic import ValidationError

from paisapal.ai.prompts import build_framework_prompt
from paisapal.ai.schemas import validate_ai_report
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
