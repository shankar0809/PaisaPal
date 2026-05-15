from __future__ import annotations

from paisapal.providers.base import EvidenceSnapshot


class MockProvider:
    name = "mock"

    def collect(self, ticker: str) -> list[EvidenceSnapshot]:
        return [
            EvidenceSnapshot(
                provider=self.name,
                source_type="market",
                status="fresh",
                label=f"Mock market snapshot for {ticker}",
                payload={"ticker": ticker, "current_price": 100.0, "volume": 1_000_000},
            ),
            EvidenceSnapshot(
                provider=self.name,
                source_type="fundamentals",
                status="fresh",
                label=f"Mock fundamentals for {ticker}",
                payload={"market_cap": 1_000_000_000, "pe_ratio": 30.0},
            ),
            EvidenceSnapshot(
                provider=self.name,
                source_type="earnings",
                status="fresh",
                label=f"Mock earnings for {ticker}",
                payload={"last_report": "mock", "eps_result": "beat"},
            ),
            EvidenceSnapshot(
                provider=self.name,
                source_type="options",
                status="fresh",
                label=f"Mock options for {ticker}",
                payload={"call_volume": 10000, "put_volume": 5000, "iv": 0.45},
            ),
            EvidenceSnapshot(
                provider=self.name,
                source_type="news_sentiment",
                status="fresh",
                label=f"Mock news sentiment for {ticker}",
                payload={"sentiment": "neutral-to-bullish"},
            ),
        ]
