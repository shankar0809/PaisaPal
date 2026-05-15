from paisapal.providers.base import EvidenceSnapshot
from paisapal.providers.mock import MockProvider


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
