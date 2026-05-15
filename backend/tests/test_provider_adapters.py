from paisapal.providers.alpha_vantage import AlphaVantageProvider
from paisapal.providers.base import EvidenceSnapshot
from paisapal.providers.fmp import FmpProvider
from paisapal.providers.mock import MockProvider
from paisapal.providers.polygon import PolygonProvider


def test_mock_provider_returns_all_core_evidence_types():
    provider = MockProvider()

    evidence = provider.collect("NVDA")

    assert {item.source_type for item in evidence} == {
        "market",
        "fundamentals",
        "earnings",
        "options",
        "news_sentiment",
    }
    assert all(item.provider == "mock" for item in evidence)
    assert all(item.status == "fresh" for item in evidence)


def test_evidence_snapshot_source_row_includes_retrieved_at():
    snapshot = EvidenceSnapshot(
        provider="mock",
        source_type="market",
        status="fresh",
        label="Known timestamp",
        payload={"ticker": "NVDA"},
        retrieved_at="2026-01-02T03:04:05+00:00",
    )

    source_row = snapshot.as_source_row()

    assert source_row["retrieved_at"] == "2026-01-02T03:04:05+00:00"


def test_unconfigured_real_providers_return_missing_snapshots():
    providers = [
        AlphaVantageProvider(api_key=None),
        FmpProvider(api_key=None),
        PolygonProvider(api_key=None),
    ]

    for provider in providers:
        evidence = provider.collect("NVDA")
        assert len(evidence) == 1
        assert evidence[0].status == "missing"
        assert "API key is not configured" in evidence[0].warnings
