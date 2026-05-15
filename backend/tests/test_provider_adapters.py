from paisapal.providers.alpha_vantage import AlphaVantageProvider
from paisapal.providers.base import EvidenceSnapshot
from paisapal.providers.fmp import FmpProvider
from paisapal.providers.mock import MockProvider
from paisapal.providers.polygon import PolygonProvider


class FakeAlphaVantageResponse:
    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload

    def raise_for_status(self):
        return None


class FakeAlphaVantageClient:
    def __init__(self, payloads):
        self.payloads = payloads
        self.calls = []

    def get(self, url, *, params, timeout):
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        return FakeAlphaVantageResponse(self.payloads[params["function"]])


class FakeFmpResponse:
    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload

    def raise_for_status(self):
        return None


class FakeFmpClient:
    def __init__(self, payloads):
        self.payloads = payloads
        self.calls = []

    def get(self, url, *, params, timeout):
        endpoint = url.rsplit("/", 1)[-1]
        self.calls.append({"url": url, "endpoint": endpoint, "params": params, "timeout": timeout})
        return FakeFmpResponse(self.payloads[endpoint])


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


def test_unconfigured_real_providers_return_missing_snapshots(monkeypatch):
    monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
    monkeypatch.delenv("FMP_API_KEY", raising=False)
    monkeypatch.delenv("POLYGON_API_KEY", raising=False)

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


def test_alpha_vantage_provider_collects_live_evidence_snapshots():
    http_client = FakeAlphaVantageClient(
        {
            "TIME_SERIES_DAILY": {
                "Meta Data": {"3. Last Refreshed": "2026-05-14"},
                "Time Series (Daily)": {
                    "2026-05-14": {
                        "1. open": "100.00",
                        "2. high": "110.00",
                        "3. low": "99.00",
                        "4. close": "108.50",
                        "5. volume": "1234567",
                    }
                },
            },
            "OVERVIEW": {
                "Symbol": "NVDA",
                "Name": "NVIDIA Corporation",
                "Sector": "Technology",
                "Industry": "Semiconductors",
                "MarketCapitalization": "5000000000",
                "PERatio": "45.2",
                "EPS": "4.56",
            },
            "EARNINGS": {
                "symbol": "NVDA",
                "quarterlyEarnings": [
                    {
                        "fiscalDateEnding": "2026-01-31",
                        "reportedEPS": "1.23",
                        "estimatedEPS": "1.20",
                        "surprise": "0.03",
                        "surprisePercentage": "2.5",
                    }
                ],
            },
            "NEWS_SENTIMENT": {
                "feed": [
                    {
                        "title": "NVIDIA news",
                        "url": "https://example.com/nvda",
                        "time_published": "20260515T120000",
                        "overall_sentiment_label": "Bullish",
                        "overall_sentiment_score": 0.25,
                    }
                ]
            },
        }
    )
    provider = AlphaVantageProvider(api_key="demo-key", http_client=http_client)

    evidence = provider.collect("NVDA")

    assert {item.source_type for item in evidence} == {
        "market",
        "fundamentals",
        "earnings",
        "news_sentiment",
    }
    assert all(item.provider == "alpha_vantage" for item in evidence)
    assert all(item.status == "fresh" for item in evidence)
    market = next(item for item in evidence if item.source_type == "market")
    assert market.payload["latest_close"] == 108.5
    assert market.payload["volume"] == 1234567
    fundamentals = next(item for item in evidence if item.source_type == "fundamentals")
    assert fundamentals.payload["name"] == "NVIDIA Corporation"
    assert fundamentals.payload["market_cap"] == 5000000000
    earnings = next(item for item in evidence if item.source_type == "earnings")
    assert earnings.payload["quarterly_earnings"][0]["reported_eps"] == 1.23
    news = next(item for item in evidence if item.source_type == "news_sentiment")
    assert news.payload["articles"][0]["sentiment_label"] == "Bullish"

    assert [call["params"]["function"] for call in http_client.calls] == [
        "TIME_SERIES_DAILY",
        "OVERVIEW",
        "EARNINGS",
        "NEWS_SENTIMENT",
    ]
    assert http_client.calls[0]["params"]["symbol"] == "NVDA"
    assert http_client.calls[1]["params"]["symbol"] == "NVDA"
    assert http_client.calls[2]["params"]["symbol"] == "NVDA"
    assert http_client.calls[3]["params"]["tickers"] == "NVDA"
    assert all(call["params"]["apikey"] == "demo-key" for call in http_client.calls)


def test_alpha_vantage_provider_returns_error_snapshot_for_provider_warning():
    http_client = FakeAlphaVantageClient({"TIME_SERIES_DAILY": {"Note": "API call frequency exceeded"}})
    provider = AlphaVantageProvider(api_key="demo-key", http_client=http_client)

    evidence = provider.collect("NVDA")

    assert len(evidence) == 1
    assert evidence[0].source_type == "provider_status"
    assert evidence[0].status == "error"
    assert evidence[0].payload["function"] == "TIME_SERIES_DAILY"
    assert evidence[0].warnings == ["API call frequency exceeded"]


def test_fmp_provider_collects_live_evidence_snapshots():
    http_client = FakeFmpClient(
        {
            "profile": [
                {
                    "symbol": "NVDA",
                    "companyName": "NVIDIA Corporation",
                    "sector": "Technology",
                    "industry": "Semiconductors",
                    "price": "130.25",
                    "beta": "1.75",
                    "mktCap": "5000000000",
                    "description": "Accelerated computing company",
                }
            ],
            "income-statement": [
                {
                    "date": "2026-01-31",
                    "revenue": "100000000",
                    "grossProfit": "75000000",
                    "operatingIncome": "40000000",
                    "netIncome": "30000000",
                    "eps": "1.23",
                }
            ],
            "balance-sheet-statement": [
                {
                    "date": "2026-01-31",
                    "cashAndCashEquivalents": "20000000",
                    "totalDebt": "10000000",
                    "totalAssets": "250000000",
                    "totalLiabilities": "90000000",
                    "totalStockholdersEquity": "160000000",
                }
            ],
            "cash-flow-statement": [
                {
                    "date": "2026-01-31",
                    "operatingCashFlow": "35000000",
                    "capitalExpenditure": "-5000000",
                    "freeCashFlow": "30000000",
                }
            ],
            "ratios": [
                {
                    "date": "2026-01-31",
                    "grossProfitMargin": "0.75",
                    "netProfitMargin": "0.30",
                    "currentRatio": "2.5",
                    "debtEquityRatio": "0.1",
                    "priceEarningsRatio": "45.2",
                }
            ],
            "key-metrics": [
                {
                    "date": "2026-01-31",
                    "revenuePerShare": "10.5",
                    "netIncomePerShare": "3.15",
                    "freeCashFlowPerShare": "2.75",
                    "peRatio": "45.2",
                    "enterpriseValue": "5100000000",
                }
            ],
            "financial-scores": [
                {
                    "symbol": "NVDA",
                    "altmanZScore": "12.3",
                    "piotroskiScore": "8",
                    "workingCapital": "70000000",
                }
            ],
            "earnings": [
                {
                    "date": "2026-02-20",
                    "epsActual": "1.23",
                    "epsEstimated": "1.20",
                    "revenueActual": "100000000",
                    "revenueEstimated": "98000000",
                }
            ],
        }
    )
    provider = FmpProvider(api_key="demo-key", http_client=http_client)

    evidence = provider.collect("NVDA")

    assert {item.source_type for item in evidence} == {
        "fundamentals",
        "financials",
        "ratios",
        "earnings",
    }
    assert all(item.provider == "fmp" for item in evidence)
    assert all(item.status == "fresh" for item in evidence)
    fundamentals = next(item for item in evidence if item.source_type == "fundamentals")
    assert fundamentals.payload["name"] == "NVIDIA Corporation"
    assert fundamentals.payload["market_cap"] == 5000000000
    assert fundamentals.payload["beta"] == 1.75
    financials = next(item for item in evidence if item.source_type == "financials")
    assert financials.payload["income_statements"][0]["revenue"] == 100000000
    assert financials.payload["balance_sheets"][0]["total_debt"] == 10000000
    assert financials.payload["cash_flows"][0]["free_cash_flow"] == 30000000
    ratios = next(item for item in evidence if item.source_type == "ratios")
    assert ratios.payload["ratios"][0]["gross_profit_margin"] == 0.75
    assert ratios.payload["key_metrics"][0]["enterprise_value"] == 5100000000
    assert ratios.payload["financial_scores"]["piotroski_score"] == 8
    earnings = next(item for item in evidence if item.source_type == "earnings")
    assert earnings.payload["earnings"][0]["eps_actual"] == 1.23

    assert [call["endpoint"] for call in http_client.calls] == [
        "profile",
        "income-statement",
        "balance-sheet-statement",
        "cash-flow-statement",
        "ratios",
        "key-metrics",
        "financial-scores",
        "earnings",
    ]
    assert all(call["params"]["symbol"] == "NVDA" for call in http_client.calls)
    assert all(call["params"]["apikey"] == "demo-key" for call in http_client.calls)
    assert "limit" not in http_client.calls[0]["params"]
    assert "limit" not in http_client.calls[6]["params"]
    assert all(call["params"]["limit"] for call in http_client.calls[1:6])
    assert http_client.calls[7]["params"]["limit"] == 8


def test_fmp_provider_returns_error_snapshot_for_provider_warning():
    http_client = FakeFmpClient({"profile": {"Error Message": "Invalid API key"}})
    provider = FmpProvider(api_key="demo-key", http_client=http_client)

    evidence = provider.collect("NVDA")

    assert len(evidence) == 1
    assert evidence[0].source_type == "provider_status"
    assert evidence[0].status == "error"
    assert evidence[0].payload["endpoint"] == "profile"
    assert evidence[0].warnings == ["Invalid API key"]
