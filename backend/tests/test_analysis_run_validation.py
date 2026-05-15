import pytest
from pydantic import ValidationError

from paisapal.analysis_runs.models import AiReportOutput, PositionSizingScenario
from paisapal.analysis_runs.validation import parse_tickers


def test_parse_tickers_accepts_commas_lines_and_spaces():
    assert parse_tickers(" nvda, tsla\ncoin  ") == ["NVDA", "TSLA", "COIN"]


def test_parse_tickers_removes_duplicates_preserving_order():
    assert parse_tickers("NVDA, tsla, nvda, TSLA, hood") == ["NVDA", "TSLA", "HOOD"]


def test_parse_tickers_rejects_malformed_symbols():
    with pytest.raises(ValueError, match="Invalid ticker: BRK/B"):
        parse_tickers("NVDA, BRK/B")


def test_parse_tickers_rejects_empty_input():
    with pytest.raises(ValueError, match="Enter at least one ticker"):
        parse_tickers(" , \n ")


def _valid_report_kwargs() -> dict:
    return {
        "ticker": "NVDA",
        "company_name": "NVIDIA Corporation",
        "current_price": 900.0,
        "final_classification": "Watchlist",
        "confidence": "medium",
        "technical_rating": "constructive",
        "vcp_rating": "forming",
        "fundamental_rating": "strong",
        "earnings_rating": "strong",
        "sentiment_rating": "positive",
        "options_flow_rating": "neutral",
        "markdown_report": "Report body",
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("entry", 0),
        ("stop", -1),
        ("risk_per_share", 0),
        ("shares_at_max_risk", -1),
    ],
)
def test_position_sizing_rejects_invalid_numeric_values(field, value):
    kwargs = {
        "label": "base case",
        "entry": 100.0,
        "stop": 95.0,
        "risk_per_share": 5.0,
        "shares_at_max_risk": 100,
        field: value,
    }

    with pytest.raises(ValidationError):
        PositionSizingScenario(**kwargs)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("current_price", 0),
        ("risk_reward", -1),
    ],
)
def test_ai_report_rejects_invalid_numeric_values(field, value):
    kwargs = _valid_report_kwargs()
    kwargs[field] = value

    with pytest.raises(ValidationError):
        AiReportOutput(**kwargs)
