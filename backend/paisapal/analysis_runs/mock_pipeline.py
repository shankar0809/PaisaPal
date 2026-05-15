from __future__ import annotations


def build_mock_report(ticker: str) -> dict:
    company = {
        "NVDA": "NVIDIA Corporation",
        "TSLA": "Tesla",
        "COIN": "Coinbase Global",
        "HOOD": "Robinhood Markets",
        "INTC": "Intel Corporation",
        "MU": "Micron Technology",
    }.get(ticker, f"{ticker} Corporation")
    markdown = f"""# {company} ({ticker}) - Stock Analysis Report

## 1. Current Stock Context

Mock current context for {ticker}. This generated report verifies the ticker-run workflow
before live providers and GPT are connected.

## 2. VCP / Technical Pattern View

Watchlist candidate. Breakout confirmation is required.

## 3. Entry, Stop-Loss, and Target Zones

Preferred setup: wait for a confirmed breakout or a controlled pullback.

## 4. SEPA-Style Position Sizing

Use 0.25%-0.5% account risk for this mocked setup.

## 5. Earnings Review

Earnings evidence is mocked in this phase.

## 6. Fundamental Metrics

Fundamental evidence is mocked in this phase.

## 7. Market Sentiment

Sentiment evidence is mocked in this phase.

## 8. Options Flow / Implied Move

Options evidence is mocked in this phase.

## 9. Final View

{ticker} classification: Watchlist.
"""
    return {
        "ticker": ticker,
        "company_name": company,
        "current_price": 100.0,
        "final_classification": "Watchlist",
        "confidence": "Low",
        "technical_rating": "Mock constructive",
        "vcp_rating": "Watchlist candidate",
        "fundamental_rating": "Mock incomplete",
        "earnings_rating": "Mock incomplete",
        "sentiment_rating": "Mock incomplete",
        "options_flow_rating": "Mock incomplete",
        "risk_reward": 2.0,
        "entry_zones": ["Breakout above resistance", "Pullback to support"],
        "stop_zones": ["Below recent support"],
        "target_zones": ["Target 1", "Target 2"],
        "position_sizing": [],
        "bullish_factors": ["Ticker-run workflow verified"],
        "bearish_risks": ["Live data not connected in mock phase"],
        "data_warnings": ["Mock report; do not use for decisions"],
        "source_summary": [
            {
                "provider": "mock",
                "retrieved_at": "mock",
                "status": "fresh",
                "label": "Mock source",
                "url": None,
                "warnings": ["Mock data"],
            }
        ],
        "markdown_report": markdown,
    }


def build_mock_sources(ticker: str) -> list[dict]:
    return [
        {
            "provider": "mock",
            "source_type": "market",
            "status": "fresh",
            "label": f"Mock market data for {ticker}",
            "url": None,
            "payload": {"ticker": ticker, "price": 100.0},
            "warnings": ["Mock source used before live adapters are connected"],
        }
    ]
