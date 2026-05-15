import pytest

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
