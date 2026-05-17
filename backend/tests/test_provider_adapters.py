from datetime import date

import httpx

from paisapal.providers.alpha_vantage import AlphaVantageProvider
from paisapal.providers.base import EvidenceSnapshot, redact_url_secrets
from paisapal.providers.finnhub import FinnhubProvider
from paisapal.providers.fmp import FmpProvider
from paisapal.providers.fred import FredProvider
from paisapal.providers.mock import MockProvider
from paisapal.providers.polygon import PolygonProvider
from paisapal.providers.sec_edgar import SecEdgarProvider
from paisapal.providers.simfin import SimFinProvider
from paisapal.providers.stooq import StooqProvider
from paisapal.providers.tiingo import TiingoProvider
from paisapal.providers.yahoo import YahooFinanceProvider


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


class FakePolygonResponse:
    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload

    def raise_for_status(self):
        return None


class FakePolygonClient:
    def __init__(self, payloads):
        self.payloads = payloads
        self.calls = []

    def get(self, url, *, params, timeout):
        path = url.removeprefix("https://api.polygon.io")
        self.calls.append({"url": url, "path": path, "params": params, "timeout": timeout})
        return FakePolygonResponse(self.payloads[path])


class FakeYahooResponse:
    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload

    def raise_for_status(self):
        return None


class FakeYahooClient:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get(self, url, *, params, timeout, headers=None):
        self.calls.append({"url": url, "params": params, "timeout": timeout, "headers": headers})
        return FakeYahooResponse(self.payload)


class FakeSecResponse:
    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload

    def raise_for_status(self):
        return None


class FakeSecClient:
    def __init__(self, payloads):
        self.payloads = payloads
        self.calls = []

    def get(self, url, *, headers, timeout):
        self.calls.append({"url": url, "headers": headers, "timeout": timeout})
        if url.endswith("/company_tickers.json"):
            return FakeSecResponse(self.payloads["tickers"])
        return FakeSecResponse(self.payloads["companyfacts"])


class FakeStooqResponse:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        return None


class FakeStooqClient:
    def __init__(self, text):
        self.text = text
        self.calls = []

    def get(self, url, *, params, timeout):
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        return FakeStooqResponse(self.text)


class FakePathResponse:
    def __init__(self, payload, error=None):
        self.payload = payload
        self.error = error

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.error is not None:
            raise self.error
        return None


class FakePathClient:
    def __init__(self, payloads):
        self.payloads = payloads
        self.calls = []

    def get(self, url, *, params=None, headers=None, timeout):
        path = url.split("://", 1)[-1].split("/", 1)[-1]
        path = "/" + path
        self.calls.append({"url": url, "path": path, "params": params or {}, "headers": headers or {}, "timeout": timeout})
        payload = self.payloads[path]
        if isinstance(payload, Exception):
            return FakePathResponse({}, payload)
        return FakePathResponse(payload)


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


def test_redact_url_secrets_removes_provider_api_keys_from_warning_text():
    warning = (
        "Client error for url "
        "'https://example.test/query?symbol=NVDA&apikey=secret-one&apiKey=secret-two'"
    )

    redacted = redact_url_secrets(warning)

    assert "secret-one" not in redacted
    assert "secret-two" not in redacted
    assert "apikey=[REDACTED]" in redacted
    assert "apiKey=[REDACTED]" in redacted


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


def test_yahoo_provider_collects_market_and_technical_snapshots():
    payload = {
        "chart": {
            "result": [
                {
                    "meta": {
                        "symbol": "NVDA",
                        "longName": "NVIDIA Corporation",
                        "regularMarketPrice": 130.5,
                        "previousClose": 127.25,
                        "currency": "USD",
                        "exchangeName": "NMS",
                    },
                    "timestamp": [1, 2, 3],
                    "indicators": {
                        "quote": [
                            {
                                "open": [100.0, 101.0, 102.0],
                                "high": [101.0, 103.0, 104.0],
                                "low": [99.0, 100.0, 101.0],
                                "close": [100.5, 102.5, 103.5],
                                "volume": [1000, 2000, 3000],
                            }
                        ]
                    },
                }
            ]
        }
    }
    http_client = FakeYahooClient(payload)
    provider = YahooFinanceProvider(http_client=http_client)

    evidence = provider.collect("NVDA")

    assert {item.source_type for item in evidence} == {"market", "technicals"}
    market = next(item for item in evidence if item.source_type == "market")
    assert market.provider == "yahoo"
    assert market.payload["ticker"] == "NVDA"
    assert market.payload["name"] == "NVIDIA Corporation"
    assert market.payload["session"]["price"] == 130.5
    technicals = next(item for item in evidence if item.source_type == "technicals")
    assert technicals.payload["latest_close"] == 103.5
    assert technicals.payload["range_high"] == 104.0
    assert technicals.payload["range_low"] == 99.0
    assert technicals.payload["average_volume"] == 2000
    assert len(technicals.payload["bars"]) == 3
    assert http_client.calls[0]["params"]["range"] == "6mo"
    assert http_client.calls[0]["params"]["interval"] == "1d"


def test_sec_edgar_provider_collects_fundamental_financial_and_ratio_snapshots():
    http_client = FakeSecClient(
        {
            "tickers": {
                "0": {"ticker": "NVDA", "cik_str": 1045810, "title": "NVIDIA CORP"}
            },
            "companyfacts": {
                "facts": {
                    "us-gaap": {
                        "Revenues": {
                            "units": {
                                "USD": [
                                    {"fy": 2025, "fp": "FY", "form": "10-K", "val": 130497000000}
                                ]
                            }
                        },
                        "NetIncomeLoss": {
                            "units": {
                                "USD": [
                                    {"fy": 2025, "fp": "FY", "form": "10-K", "val": 72880000000}
                                ]
                            }
                        },
                        "Assets": {
                            "units": {
                                "USD": [
                                    {"fy": 2025, "fp": "FY", "form": "10-K", "val": 111601000000}
                                ]
                            }
                        },
                        "Liabilities": {
                            "units": {
                                "USD": [
                                    {"fy": 2025, "fp": "FY", "form": "10-K", "val": 32274000000}
                                ]
                            }
                        },
                        "StockholdersEquity": {
                            "units": {
                                "USD": [
                                    {"fy": 2025, "fp": "FY", "form": "10-K", "val": 79327000000}
                                ]
                            }
                        },
                        "OperatingCashFlow": {
                            "units": {
                                "USD": [
                                    {"fy": 2025, "fp": "FY", "form": "10-K", "val": 64089000000}
                                ]
                            }
                        },
                    }
                }
            },
        }
    )
    provider = SecEdgarProvider(http_client=http_client, user_agent="PaisaPal test contact@example.com")

    evidence = provider.collect("NVDA")

    assert {item.source_type for item in evidence} == {"fundamentals", "financials", "ratios"}
    fundamentals = next(item for item in evidence if item.source_type == "fundamentals")
    assert fundamentals.provider == "sec_edgar"
    assert fundamentals.payload["ticker"] == "NVDA"
    assert fundamentals.payload["name"] == "NVIDIA CORP"
    assert fundamentals.payload["cik"] == "0001045810"
    financials = next(item for item in evidence if item.source_type == "financials")
    assert financials.payload["income_statement"]["revenue"] == 130497000000
    assert financials.payload["balance_sheet"]["assets"] == 111601000000
    ratios = next(item for item in evidence if item.source_type == "ratios")
    assert ratios.payload["net_margin"] == 0.5585
    assert ratios.payload["debt_to_assets"] == 0.2892
    assert all(
        call["headers"]["User-Agent"] == "PaisaPal test contact@example.com"
        for call in http_client.calls
    )


def test_stooq_provider_collects_market_and_technical_snapshots():
    csv_text = "\n".join(
        [
            "Date,Open,High,Low,Close,Volume",
            "2026-05-13,100,103,99,102,1000",
            "2026-05-14,102,106,101,105,2000",
            "2026-05-15,105,108,104,107,3000",
        ]
    )
    http_client = FakeStooqClient(csv_text)
    provider = StooqProvider(http_client=http_client)

    evidence = provider.collect("NVDA")

    assert {item.source_type for item in evidence} == {"market", "technicals"}
    market = next(item for item in evidence if item.source_type == "market")
    assert market.provider == "stooq"
    assert market.payload["ticker"] == "NVDA"
    assert market.payload["session"]["price"] == 107.0
    technicals = next(item for item in evidence if item.source_type == "technicals")
    assert technicals.payload["latest_close"] == 107.0
    assert technicals.payload["range_high"] == 108.0
    assert technicals.payload["range_low"] == 99.0
    assert technicals.payload["average_volume"] == 2000
    assert http_client.calls[0]["params"]["s"] == "nvda.us"
    assert http_client.calls[0]["params"] == {"s": "nvda.us", "i": "d"}


def test_stooq_provider_uses_direct_csv_without_api_key():
    csv_text = "\n".join(
        [
            "Date,Open,High,Low,Close,Volume",
            "2026-05-14,100,110,99,108,1234567",
            "2026-05-15,101,111,100,109,2345678",
        ]
    )
    http_client = FakeStooqClient(csv_text)
    provider = StooqProvider(http_client=http_client)

    evidence = provider.collect("NVDA")

    assert {item.source_type for item in evidence} == {"market", "technicals"}
    assert all(item.status == "fresh" for item in evidence)
    assert evidence[0].payload["ticker"] == "NVDA"
    assert http_client.calls[0]["params"] == {"s": "nvda.us", "i": "d"}


def test_stooq_provider_falls_back_to_datareader_when_csv_is_empty():
    provider = StooqProvider(http_client=FakeStooqClient(""))
    provider._request_direct_csv = lambda ticker: []  # type: ignore[method-assign]
    provider._request_via_datareader = lambda ticker: [  # type: ignore[method-assign]
        {"date": "2026-05-15", "open": 100.0, "high": 110.0, "low": 99.0, "close": 108.0, "volume": 1234567}
    ]

    evidence = provider.collect("NVDA")

    assert {item.source_type for item in evidence} == {"market", "technicals"}
    assert evidence[0].payload["session"]["price"] == 108.0


def test_tiingo_provider_collects_market_technical_and_news_snapshots():
    http_client = FakePathClient(
        {
            "/tiingo/daily/NVDA/prices": [
                {"date": "2026-05-13T00:00:00.000Z", "open": 100, "high": 103, "low": 99, "close": 102, "volume": 1000},
                {"date": "2026-05-14T00:00:00.000Z", "open": 102, "high": 106, "low": 101, "close": 105, "volume": 2000},
                {"date": "2026-05-15T00:00:00.000Z", "open": 105, "high": 108, "low": 104, "close": 107, "volume": 3000},
            ],
            "/tiingo/news": [
                {
                    "title": "NVIDIA launches product",
                    "url": "https://example.com/nvda",
                    "publishedDate": "2026-05-15T12:00:00Z",
                    "description": "Product news",
                    "source": "Example",
                }
            ],
        }
    )
    provider = TiingoProvider(api_key="tiingo-key", http_client=http_client)

    evidence = provider.collect("NVDA")

    assert {item.source_type for item in evidence} == {"market", "technicals", "news_sentiment"}
    market = next(item for item in evidence if item.source_type == "market")
    assert market.payload["ticker"] == "NVDA"
    assert market.payload["session"]["price"] == 107.0
    technicals = next(item for item in evidence if item.source_type == "technicals")
    assert technicals.payload["latest_close"] == 107.0
    assert technicals.payload["range_high"] == 108.0
    assert technicals.payload["average_volume"] == 2000
    news = next(item for item in evidence if item.source_type == "news_sentiment")
    assert news.payload["articles"][0]["title"] == "NVIDIA launches product"
    assert all(call["headers"]["Authorization"] == "Token tiingo-key" for call in http_client.calls)
    assert http_client.calls[0]["params"]["resampleFreq"] == "daily"
    assert http_client.calls[1]["params"]["tickers"] == "NVDA"


def test_tiingo_provider_keeps_price_snapshots_when_news_is_plan_gated():
    http_client = FakePathClient(
        {
            "/tiingo/daily/NVDA/prices": [
                {"date": "2026-05-15T00:00:00.000Z", "open": 105, "high": 108, "low": 104, "close": 107, "volume": 3000},
            ],
            "/tiingo/news": {"detail": "Forbidden"},
        }
    )
    provider = TiingoProvider(api_key="tiingo-key", http_client=http_client)

    evidence = provider.collect("NVDA")

    assert {"market", "technicals", "provider_status"} == {item.source_type for item in evidence}
    assert next(item for item in evidence if item.source_type == "market").payload["session"]["price"] == 107.0
    error = next(item for item in evidence if item.source_type == "provider_status")
    assert error.payload["endpoint"] == "news"
    assert error.warnings == ["Forbidden"]


def test_finnhub_provider_collects_market_earnings_and_news_snapshots():
    http_client = FakePathClient(
        {
            "/api/v1/quote": {"c": 130.5, "pc": 127.25, "h": 132.0, "l": 126.5, "o": 128.0, "t": 1778880000},
            "/api/v1/stock/earnings": [
                {"period": "2026-03-31", "actual": 1.23, "estimate": 1.20, "surprise": 0.03, "surprisePercent": 2.5}
            ],
            "/api/v1/company-news": [
                {"headline": "NVIDIA earnings beat", "url": "https://example.com/news", "datetime": 1778880000, "source": "Example"}
            ],
            "/api/v1/stock/option-chain": {
                "data": [
                    {
                        "expirationDate": "2026-06-20",
                        "options": {
                            "CALL": [
                                {
                                    "symbol": "NVDA260620C00130000",
                                    "strike": 130,
                                    "lastPrice": 8.2,
                                    "bid": 8.1,
                                    "ask": 8.4,
                                    "volume": 500,
                                    "openInterest": 12000,
                                    "impliedVolatility": 0.55,
                                }
                            ]
                        },
                    }
                ]
            },
        }
    )
    provider = FinnhubProvider(api_key="finnhub-key", http_client=http_client)

    evidence = provider.collect("NVDA")

    assert {item.source_type for item in evidence} == {"market", "earnings", "news_sentiment", "options"}
    market = next(item for item in evidence if item.source_type == "market")
    assert market.payload["session"]["price"] == 130.5
    earnings = next(item for item in evidence if item.source_type == "earnings")
    assert earnings.payload["earnings"][0]["eps_actual"] == 1.23
    news = next(item for item in evidence if item.source_type == "news_sentiment")
    assert news.payload["articles"][0]["title"] == "NVIDIA earnings beat"
    options = next(item for item in evidence if item.source_type == "options")
    assert options.payload["contracts"][0]["strike_price"] == 130.0
    assert options.payload["contracts"][0]["implied_volatility"] == 0.55
    assert all(call["params"]["token"] == "finnhub-key" for call in http_client.calls)
    assert http_client.calls[0]["params"]["symbol"] == "NVDA"
    assert http_client.calls[1]["params"]["symbol"] == "NVDA"
    assert http_client.calls[2]["params"]["symbol"] == "NVDA"
    assert http_client.calls[3]["params"]["symbol"] == "NVDA"


def test_finnhub_provider_keeps_earnings_and_news_when_option_chain_is_plan_gated():
    http_client = FakePathClient(
        {
            "/api/v1/quote": {"c": 130.5, "pc": 127.25},
            "/api/v1/stock/earnings": [{"period": "2026-03-31", "actual": 1.23, "estimate": 1.20}],
            "/api/v1/company-news": [{"headline": "NVIDIA earnings beat", "url": "https://example.com/news"}],
            "/api/v1/stock/option-chain": {"error": "Forbidden"},
        }
    )
    provider = FinnhubProvider(api_key="finnhub-key", http_client=http_client)

    evidence = provider.collect("NVDA")

    assert {"market", "earnings", "news_sentiment", "provider_status"} == {
        item.source_type for item in evidence
    }
    assert next(item for item in evidence if item.source_type == "earnings").payload["earnings"][0]["eps_actual"] == 1.23
    assert next(item for item in evidence if item.source_type == "news_sentiment").payload["articles"][0]["title"] == "NVIDIA earnings beat"
    error = next(item for item in evidence if item.source_type == "provider_status")
    assert error.payload["endpoint"] == "option-chain"
    assert error.status == "missing"
    assert error.warnings == ["Forbidden"]


def test_finnhub_provider_treats_auth_failures_as_missing_snapshots():
    request = httpx.Request("GET", "https://finnhub.io/api/v1/stock/option-chain")
    response = httpx.Response(403, request=request)
    http_error = httpx.HTTPStatusError("Client error '403 Forbidden'", request=request, response=response)
    http_client = FakePathClient(
        {
            "/api/v1/quote": {"c": 130.5, "pc": 127.25},
            "/api/v1/stock/earnings": [{"period": "2026-03-31", "actual": 1.23, "estimate": 1.20}],
            "/api/v1/company-news": [{"headline": "NVIDIA earnings beat", "url": "https://example.com/news"}],
            "/api/v1/stock/option-chain": http_error,
        }
    )
    provider = FinnhubProvider(api_key="finnhub-key", http_client=http_client)

    evidence = provider.collect("NVDA")

    assert {"market", "earnings", "news_sentiment", "provider_status"} == {
        item.source_type for item in evidence
    }
    error = next(item for item in evidence if item.source_type == "provider_status")
    assert error.status == "missing"
    assert error.payload["endpoint"] == "option-chain"


def test_simfin_provider_collects_fundamental_financial_and_ratio_snapshots():
    http_client = FakePathClient(
        {
            "/api/v3/companies/general/compact": [
                {
                    "ticker": "NVDA",
                    "name": "NVIDIA Corporation",
                    "sector": "Technology",
                    "industry": "Semiconductors",
                    "market": "us",
                    "companyDescription": "Accelerated computing company",
                }
            ],
            "/api/v3/companies/statements/compact": {
                "statements": [
                    {
                        "period": "FY",
                        "fyear": 2026,
                        "incomeStatement": {"Revenue": 100000000, "Gross Profit": 75000000, "Net Income": 30000000},
                        "balanceSheet": {"Total Assets": 250000000, "Total Liabilities": 90000000, "Total Equity": 160000000},
                        "cashFlow": {"Net Cash from Operating Activities": 35000000, "Capital Expenditure": -5000000},
                    }
                ]
            },
        }
    )
    provider = SimFinProvider(api_key="simfin-key", http_client=http_client)

    evidence = provider.collect("NVDA")

    assert {item.source_type for item in evidence} == {"fundamentals", "financials", "ratios"}
    fundamentals = next(item for item in evidence if item.source_type == "fundamentals")
    assert fundamentals.payload["name"] == "NVIDIA Corporation"
    financials = next(item for item in evidence if item.source_type == "financials")
    assert financials.payload["income_statement"]["revenue"] == 100000000
    ratios = next(item for item in evidence if item.source_type == "ratios")
    assert ratios.payload["gross_margin"] == 0.75
    assert ratios.payload["debt_to_assets"] == 0.36
    assert all(call["params"]["api-key"] == "simfin-key" for call in http_client.calls)
    assert all(call["params"]["ticker"] == "NVDA" for call in http_client.calls)


def test_simfin_provider_treats_401_auth_failures_as_missing_snapshots():
    request = httpx.Request("GET", "https://backend.simfin.com/api/v3/companies/general/compact")
    response = httpx.Response(401, request=request)
    http_error = httpx.HTTPStatusError("Client error '401 Unauthorized'", request=request, response=response)
    http_client = FakePathClient(
        {
            "/api/v3/companies/general/compact": http_error,
            "/api/v3/companies/statements/compact": {
                "statements": [
                    {
                        "period": "FY",
                        "fyear": 2026,
                        "incomeStatement": {"Revenue": 100000000, "Gross Profit": 75000000, "Net Income": 30000000},
                        "balanceSheet": {"Total Assets": 250000000, "Total Liabilities": 90000000, "Total Equity": 160000000},
                        "cashFlow": {"Net Cash from Operating Activities": 35000000, "Capital Expenditure": -5000000},
                    }
                ]
            },
        }
    )
    provider = SimFinProvider(api_key="simfin-key", http_client=http_client)

    evidence = provider.collect("NVDA")

    assert len(evidence) == 1
    assert evidence[0].source_type == "provider_status"
    assert evidence[0].status == "missing"
    assert evidence[0].payload["endpoint"] == "companies"


def test_fred_provider_collects_macro_snapshots():
    http_client = FakePathClient(
        {
            "/fred/series/observations": {
                "observations": [
                    {"date": "2026-04-01", "value": "4.2"},
                    {"date": "2026-03-01", "value": "4.1"},
                ]
            }
        }
    )
    provider = FredProvider(api_key="fred-key", http_client=http_client, series_ids=["FEDFUNDS", "CPIAUCSL"])

    evidence = provider.collect("NVDA")

    assert {item.source_type for item in evidence} == {"macro"}
    assert len(evidence) == 2
    assert evidence[0].payload["series_id"] == "FEDFUNDS"
    assert evidence[0].payload["latest"]["value"] == 4.2
    assert all(call["params"]["api_key"] == "fred-key" for call in http_client.calls)
    assert all(call["params"]["file_type"] == "json" for call in http_client.calls)
    assert all(call["params"]["sort_order"] == "desc" for call in http_client.calls)


def test_new_keyed_providers_return_missing_snapshots_without_api_keys(monkeypatch):
    for key in ("TIINGO_API_KEY", "FINNHUB_API_KEY", "SIMFIN_API_KEY", "FRED_API_KEY"):
        monkeypatch.delenv(key, raising=False)

    providers = [
        TiingoProvider(api_key=None),
        FinnhubProvider(api_key=None),
        SimFinProvider(api_key=None),
        FredProvider(api_key=None),
    ]

    for provider in providers:
        evidence = provider.collect("NVDA")
        assert len(evidence) == 1
        assert evidence[0].source_type == "provider_status"
        assert evidence[0].status == "missing"
        assert evidence[0].warnings == ["API key is not configured"]


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


def test_fmp_provider_keeps_successful_snapshots_when_earnings_endpoint_is_plan_gated():
    http_client = FakeFmpClient(
        {
            "profile": [{"symbol": "NVDA", "companyName": "NVIDIA Corporation", "mktCap": "5000000000"}],
            "income-statement": [{"date": "2026-01-31", "revenue": "100000000"}],
            "balance-sheet-statement": [{"date": "2026-01-31", "totalAssets": "250000000"}],
            "cash-flow-statement": [{"date": "2026-01-31", "freeCashFlow": "30000000"}],
            "ratios": [{"date": "2026-01-31", "grossProfitMargin": "0.75"}],
            "key-metrics": [{"date": "2026-01-31", "enterpriseValue": "5100000000"}],
            "financial-scores": [{"piotroskiScore": "8"}],
            "earnings": {"Error Message": "Payment Required"},
        }
    )
    provider = FmpProvider(api_key="demo-key", http_client=http_client)

    evidence = provider.collect("NVDA")

    assert {"fundamentals", "financials", "ratios", "provider_status"} == {
        item.source_type for item in evidence
    }
    error = next(item for item in evidence if item.source_type == "provider_status")
    assert error.payload["endpoint"] == "earnings"
    assert error.warnings == ["Payment Required"]


def test_polygon_provider_collects_live_evidence_snapshots():
    bars = [
        {"t": index, "o": 100.0 + index, "h": 102.0 + index, "l": 99.0 + index, "c": 101.0 + index, "v": 1_500_000}
        for index in range(30)
    ]
    http_client = FakePolygonClient(
        {
            "/v3/reference/tickers/NVDA": {
                "status": "OK",
                "results": {
                    "ticker": "NVDA",
                    "name": "NVIDIA Corporation",
                    "market": "stocks",
                    "primary_exchange": "XNAS",
                    "type": "CS",
                    "market_cap": 5_000_000_000,
                    "sic_description": "Semiconductors",
                },
            },
            "/v3/snapshot": {
                "status": "OK",
                "results": [
                    {
                        "ticker": "NVDA",
                        "session": {
                            "price": 130.0,
                            "change": 2.5,
                            "change_percent": 1.96,
                            "volume": 2_000_000,
                            "previous_close": 127.5,
                        },
                        "last_trade": {"price": 130.1, "sip_timestamp": 1_779_000_000_000_000_000},
                    }
                ],
            },
            "/v2/aggs/ticker/NVDA/range/1/day/2026-01-15/2026-05-15": {
                "status": "OK",
                "results": bars,
            },
            "/v3/snapshot/options/NVDA": {
                "status": "OK",
                "results": [
                    {
                        "details": {
                            "ticker": "O:NVDA260620C00130000",
                            "contract_type": "call",
                            "strike_price": 130.0,
                            "expiration_date": "2026-06-20",
                        },
                        "implied_volatility": 0.55,
                        "open_interest": 12_000,
                        "break_even_price": 138.5,
                        "greeks": {"delta": 0.62, "gamma": 0.02, "theta": -0.05, "vega": 0.18},
                        "day": {"change": 1.1, "change_percent": 4.2, "volume": 5_000},
                        "underlying_asset": {"price": 130.0},
                    }
                ],
            },
        }
    )
    provider = PolygonProvider(api_key="demo-key", http_client=http_client, end_date=date(2026, 5, 15))

    evidence = provider.collect("NVDA")

    assert {item.source_type for item in evidence} == {"market", "technicals", "options"}
    assert all(item.provider == "polygon" for item in evidence)
    assert all(item.status == "fresh" for item in evidence)
    market = next(item for item in evidence if item.source_type == "market")
    assert market.payload["ticker"] == "NVDA"
    assert market.payload["name"] == "NVIDIA Corporation"
    assert market.payload["session"]["price"] == 130.0
    technicals = next(item for item in evidence if item.source_type == "technicals")
    assert technicals.payload["latest_close"] == 130.0
    assert technicals.payload["sma_20"] == 120.5
    assert technicals.payload["range_high"] == 131.0
    assert technicals.payload["range_low"] == 99.0
    assert technicals.payload["average_volume"] == 1500000
    options = next(item for item in evidence if item.source_type == "options")
    assert options.payload["contracts"][0]["implied_volatility"] == 0.55
    assert options.payload["contracts"][0]["open_interest"] == 12000
    assert options.payload["contracts"][0]["delta"] == 0.62
    assert options.payload["contracts"][0]["strike_price"] == 130.0
    assert options.payload["contracts"][0]["expiration_date"] == "2026-06-20"
    assert options.payload["contracts"][0]["underlying_price"] == 130.0

    assert [call["path"] for call in http_client.calls] == [
        "/v3/reference/tickers/NVDA",
        "/v3/snapshot",
        "/v2/aggs/ticker/NVDA/range/1/day/2026-01-15/2026-05-15",
        "/v3/snapshot/options/NVDA",
    ]
    assert all(call["params"]["apiKey"] == "demo-key" for call in http_client.calls)
    assert http_client.calls[1]["params"]["ticker"] == "NVDA"
    assert http_client.calls[1]["params"]["type"] == "stocks"
    assert http_client.calls[2]["params"]["adjusted"] is True
    assert http_client.calls[2]["params"]["sort"] == "asc"
    assert http_client.calls[2]["params"]["limit"] == 120
    assert http_client.calls[3]["params"]["limit"] == 20


def test_polygon_provider_returns_error_snapshot_for_provider_warning():
    http_client = FakePolygonClient(
        {
            "/v3/reference/tickers/NVDA": {
                "status": "ERROR",
                "error": "Invalid API key",
            }
        }
    )
    provider = PolygonProvider(api_key="demo-key", http_client=http_client)

    evidence = provider.collect("NVDA")

    assert len(evidence) == 1
    assert evidence[0].source_type == "provider_status"
    assert evidence[0].status == "error"
    assert evidence[0].payload["endpoint"] == "ticker_details"
    assert evidence[0].warnings == ["Invalid API key"]


def test_polygon_provider_keeps_aggregates_when_stock_snapshot_is_plan_gated():
    bars = [{"t": index, "o": 100.0, "h": 102.0, "l": 99.0, "c": 101.0 + index, "v": 1_500_000} for index in range(30)]
    http_client = FakePolygonClient(
        {
            "/v3/reference/tickers/NVDA": {
                "status": "OK",
                "results": {"ticker": "NVDA", "name": "NVIDIA Corporation"},
            },
            "/v3/snapshot": {"status": "ERROR", "error": "Forbidden"},
            "/v2/aggs/ticker/NVDA/range/1/day/2026-01-15/2026-05-15": {
                "status": "OK",
                "results": bars,
            },
            "/v3/snapshot/options/NVDA": {"status": "ERROR", "error": "Forbidden"},
        }
    )
    provider = PolygonProvider(api_key="demo-key", http_client=http_client, end_date=date(2026, 5, 15))

    evidence = provider.collect("NVDA")

    assert {"market", "technicals", "provider_status"} == {item.source_type for item in evidence}
    assert next(item for item in evidence if item.source_type == "market").payload["name"] == "NVIDIA Corporation"
    assert next(item for item in evidence if item.source_type == "technicals").payload["latest_close"] == 130.0
    assert [item.payload["endpoint"] for item in evidence if item.source_type == "provider_status"] == [
        "stock_snapshot",
        "options_snapshot",
    ]
