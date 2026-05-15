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
