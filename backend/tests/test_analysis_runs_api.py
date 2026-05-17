import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from paisapal.api import routes
from paisapal.api.routes import get_session
from paisapal.analysis_runs.orchestrator import configured_providers
from paisapal.db.base import Base
from paisapal.db.repository import update_job_status
from paisapal.main import app


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_session():
        session = testing_session_local()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = override_get_session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_create_analysis_run_returns_jobs(client):
    response = client.post(
        "/api/analysis-runs",
        json={
            "tickers": "NVDA, TSLA",
            "account_size": 100000,
            "risk_percent": 0.5,
            "notes": "AI leaders",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "queued"
    assert [job["ticker"] for job in body["jobs"]] == ["NVDA", "TSLA"]
    assert [job["status"] for job in body["jobs"]] == ["queued", "queued"]


def test_create_analysis_run_rejects_invalid_numeric_settings(client):
    response = client.post(
        "/api/analysis-runs",
        json={
            "tickers": "NVDA",
            "account_size": -1,
            "risk_percent": 0,
            "max_dollar_risk": 0,
        },
    )

    assert response.status_code == 422


def test_run_mock_analysis_completes_run_jobs_and_creates_report(client):
    created = client.post("/api/analysis-runs", json={"tickers": "NVDA"}).json()

    response = client.post(f"/api/analysis-runs/{created['id']}/run-mock")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "complete"
    assert body["jobs"][0]["status"] == "complete"

    fetched = client.get(f"/api/analysis-runs/{created['id']}").json()
    assert fetched["status"] == "complete"

    watchlist = client.get("/api/watchlist").json()
    assert len(watchlist) == 1
    assert watchlist[0]["ticker"] == "NVDA"
    assert watchlist[0]["final_decision"] == "Watchlist"

    report = client.get("/api/tickers/NVDA").json()
    assert "Current Price: $100.00" in report["markdown_report"]
    assert "Final Classification: Watchlist" in report["markdown_report"]
    assert "source_summary" in report["report"]
    assert any(
        item["provider"] == "mock" for item in report["report"]["source_summary"]
    )
    assert {
        item["label"] for item in report["report"]["source_summary"]
    } >= {"Mock market snapshot for NVDA"}
    assert report["report"]["data_warnings"] == ["Mock report; do not use for decisions"]
    assert "analysis_steps" in report["report"]
    assert len(report["report"]["analysis_steps"]) >= 1


def test_latest_analysis_run_for_ticker_returns_most_recent_run(client):
    _first = client.post("/api/analysis-runs", json={"tickers": "NVDA"}).json()
    second = client.post("/api/analysis-runs", json={"tickers": "NVDA, AAPL"}).json()

    response = client.get("/api/analysis-runs/latest/NVDA")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == second["id"]
    assert body["tickers"] == ["NVDA", "AAPL"]
    assert [job["ticker"] for job in body["jobs"]] == ["NVDA", "AAPL"]


def test_analysis_runs_lists_recent_runs(client):
    first = client.post("/api/analysis-runs", json={"tickers": "NVDA"}).json()
    second = client.post("/api/analysis-runs", json={"tickers": "AAPL"}).json()

    response = client.get("/api/analysis-runs")

    assert response.status_code == 200
    body = response.json()
    assert [run["id"] for run in body] == [second["id"], first["id"]]
    assert body[0]["tickers"] == ["AAPL"]
    assert body[1]["tickers"] == ["NVDA"]


def test_ticker_report_includes_framework_source_coverage(client):
    created = client.post("/api/analysis-runs", json={"tickers": "NVDA"}).json()
    client.post(f"/api/analysis-runs/{created['id']}/run-mock")

    response = client.get("/api/tickers/NVDA")

    assert response.status_code == 200
    coverage = response.json()["source_coverage"]
    by_section = {item["section"]: item for item in coverage}
    assert "Current Stock Context" in by_section
    assert "Options Flow / Implied Move" in by_section
    assert by_section["Current Stock Context"]["status"] in {"covered", "partial", "missing"}
    assert by_section["Options Flow / Implied Move"]["status"] in {"covered", "partial", "missing"}


def test_run_mock_analysis_always_uses_mock_provider(client, monkeypatch):
    captured = {}

    class CapturingOrchestrator:
        def __init__(self, providers=None, ai_client=None, use_live_ai=False):
            captured["providers"] = providers
            captured["ai_client"] = ai_client
            captured["use_live_ai"] = use_live_ai

        def run_job(self, session, job):
            update_job_status(session, job.id, "complete")

    monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "demo-key")
    monkeypatch.setattr(routes, "AnalysisOrchestrator", CapturingOrchestrator)
    created = client.post("/api/analysis-runs", json={"tickers": "NVDA"}).json()

    response = client.post(f"/api/analysis-runs/{created['id']}/run-mock")

    assert response.status_code == 200
    assert [provider.name for provider in captured["providers"]] == ["mock"]
    assert captured["ai_client"] is None
    assert captured["use_live_ai"] is False


def test_run_analysis_uses_configured_providers_and_openai_client(client, monkeypatch):
    captured = {}

    class FakeProvider:
        name = "fake_live_provider"

    class FakeOpenAiClient:
        pass

    class CapturingOrchestrator:
        def __init__(self, providers=None, ai_client=None, use_live_ai=False):
            captured["providers"] = providers
            captured["ai_client"] = ai_client
            captured["use_live_ai"] = use_live_ai

        def run_job(self, session, job):
            update_job_status(session, job.id, "complete")

    live_provider = FakeProvider()
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setattr(routes, "configured_providers", lambda: [live_provider])
    monkeypatch.setattr(routes, "build_analysis_client", lambda: FakeOpenAiClient())
    monkeypatch.setattr(routes, "AnalysisOrchestrator", CapturingOrchestrator)
    created = client.post("/api/analysis-runs", json={"tickers": "NVDA"}).json()

    response = client.post(f"/api/analysis-runs/{created['id']}/run")

    assert response.status_code == 200
    assert response.json()["status"] == "complete"
    assert captured["providers"] == [live_provider]
    assert isinstance(captured["ai_client"], FakeOpenAiClient)
    assert captured["use_live_ai"] is True


def test_run_analysis_uses_ollama_client_when_selected(client, monkeypatch):
    captured = {}

    class FakeProvider:
        name = "fake_live_provider"

    class FakeOllamaClient:
        pass

    class CapturingOrchestrator:
        def __init__(self, providers=None, ai_client=None, use_live_ai=False):
            captured["providers"] = providers
            captured["ai_client"] = ai_client
            captured["use_live_ai"] = use_live_ai

        def run_job(self, session, job):
            update_job_status(session, job.id, "complete")

    live_provider = FakeProvider()
    monkeypatch.setenv("AI_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(routes, "configured_providers", lambda: [live_provider])
    monkeypatch.setattr(routes, "build_analysis_client", lambda: FakeOllamaClient())
    monkeypatch.setattr(routes, "AnalysisOrchestrator", CapturingOrchestrator)
    created = client.post("/api/analysis-runs", json={"tickers": "NVDA"}).json()

    response = client.post(f"/api/analysis-runs/{created['id']}/run")

    assert response.status_code == 200
    assert response.json()["status"] == "complete"
    assert captured["providers"] == [live_provider]
    assert isinstance(captured["ai_client"], FakeOllamaClient)
    assert captured["use_live_ai"] is True


def test_run_mock_analysis_marks_run_partial_when_jobs_are_mixed(client, monkeypatch):
    class MixedOutcomeOrchestrator:
        def __init__(self, providers=None, ai_client=None, use_live_ai=False):
            pass

        def run_job(self, session, job):
            status = "complete" if job.ticker == "NVDA" else "failed"
            update_job_status(session, job.id, status)

    monkeypatch.setattr(routes, "AnalysisOrchestrator", MixedOutcomeOrchestrator)
    created = client.post("/api/analysis-runs", json={"tickers": "NVDA, TSLA"}).json()

    response = client.post(f"/api/analysis-runs/{created['id']}/run-mock")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "partial"
    assert [job["status"] for job in body["jobs"]] == ["complete", "failed"]


def test_provider_status_includes_live_readiness_metadata(client, monkeypatch):
    monkeypatch.setenv("MARKET_DATA_MODE", "paid")
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("POLYGON_API_KEY", "polygon-key")
    monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
    monkeypatch.delenv("FMP_API_KEY", raising=False)

    response = client.get("/api/provider-status")

    assert response.status_code == 200
    body = response.json()
    by_provider = {item["provider"]: item for item in body}
    assert by_provider["openai"]["role"] == "ai"
    assert by_provider["openai"]["required_for_live"] is True
    assert by_provider["polygon"]["role"] == "market_data"
    assert all(item["live_ready"] is True for item in body)
    assert all(item["message"] == "Live AI analysis ready" for item in body)


def test_provider_status_includes_ollama_readiness_metadata(client, monkeypatch):
    monkeypatch.setenv("MARKET_DATA_MODE", "paid")
    monkeypatch.setenv("AI_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("POLYGON_API_KEY", "polygon-key")
    monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
    monkeypatch.delenv("FMP_API_KEY", raising=False)

    response = client.get("/api/provider-status")

    assert response.status_code == 200
    body = response.json()
    by_provider = {item["provider"]: item for item in body}
    assert by_provider["ollama"]["role"] == "ai"
    assert by_provider["ollama"]["configured"] is True
    assert by_provider["ollama"]["required_for_live"] is True
    assert by_provider["polygon"]["role"] == "market_data"
    assert all(item["live_ready"] is True for item in body)
    assert all(item["message"] == "Live AI analysis ready" for item in body)


def test_provider_status_reports_not_ready_without_ai_or_market_data(client, monkeypatch):
    monkeypatch.setenv("MARKET_DATA_MODE", "paid")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("POLYGON_API_KEY", raising=False)
    monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
    monkeypatch.delenv("FMP_API_KEY", raising=False)

    response = client.get("/api/provider-status")

    assert response.status_code == 200
    body = response.json()
    assert all(item["live_ready"] is False for item in body)
    assert body[0]["message"] == "Configure OPENAI_API_KEY and at least one market data provider"


def test_configured_providers_returns_alpha_vantage_when_key_is_present(monkeypatch):
    monkeypatch.setenv("MARKET_DATA_MODE", "paid")
    monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "demo-key")
    monkeypatch.delenv("FMP_API_KEY", raising=False)
    monkeypatch.delenv("POLYGON_API_KEY", raising=False)

    providers = configured_providers()

    assert [provider.name for provider in providers] == ["alpha_vantage"]


def test_configured_providers_returns_free_stack_by_default(monkeypatch):
    monkeypatch.delenv("MARKET_DATA_MODE", raising=False)
    monkeypatch.delenv("ENABLE_PAID_PROVIDER_FALLBACK", raising=False)
    monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "demo-key")
    monkeypatch.setenv("FMP_API_KEY", "fmp-key")
    monkeypatch.setenv("POLYGON_API_KEY", "polygon-key")

    providers = configured_providers()

    assert [provider.name for provider in providers] == ["yahoo", "sec_edgar", "stooq"]


def test_configured_providers_appends_paid_stack_when_free_fallback_enabled(monkeypatch):
    monkeypatch.setenv("MARKET_DATA_MODE", "free")
    monkeypatch.setenv("ENABLE_PAID_PROVIDER_FALLBACK", "true")
    monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "demo-key")
    monkeypatch.setenv("FMP_API_KEY", "fmp-key")
    monkeypatch.setenv("POLYGON_API_KEY", "polygon-key")
    monkeypatch.setenv("TIINGO_API_KEY", "tiingo-key")
    monkeypatch.setenv("FINNHUB_API_KEY", "finnhub-key")
    monkeypatch.setenv("SIMFIN_API_KEY", "simfin-key")
    monkeypatch.setenv("FRED_API_KEY", "fred-key")

    providers = configured_providers()

    assert [provider.name for provider in providers] == [
        "yahoo",
        "sec_edgar",
        "stooq",
        "alpha_vantage",
        "fmp",
        "polygon",
        "tiingo",
        "finnhub",
        "simfin",
        "fred",
    ]


def test_provider_status_reports_free_market_data_mode(client, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "ollama")
    monkeypatch.setenv("MARKET_DATA_MODE", "free")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
    monkeypatch.delenv("POLYGON_API_KEY", raising=False)
    monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
    monkeypatch.delenv("FMP_API_KEY", raising=False)
    monkeypatch.setenv("TIINGO_API_KEY", "tiingo-key")
    monkeypatch.setenv("FINNHUB_API_KEY", "finnhub-key")
    monkeypatch.setenv("SIMFIN_API_KEY", "simfin-key")
    monkeypatch.setenv("FRED_API_KEY", "fred-key")
    monkeypatch.setenv("ENABLE_PAID_PROVIDER_FALLBACK", "true")

    response = client.get("/api/provider-status")

    assert response.status_code == 200
    by_provider = {item["provider"]: item for item in response.json()}
    assert by_provider["yahoo"]["configured"] is True
    assert by_provider["sec_edgar"]["configured"] is True
    assert by_provider["stooq"]["configured"] is True
    assert by_provider["tiingo"]["configured"] is True
    assert by_provider["finnhub"]["configured"] is True
    assert by_provider["simfin"]["configured"] is True
    assert by_provider["fred"]["configured"] is True
    assert by_provider["yahoo"]["live_ready"] is True


def test_configured_providers_falls_back_to_mock_without_provider_keys(monkeypatch):
    monkeypatch.setenv("MARKET_DATA_MODE", "paid")
    monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
    monkeypatch.delenv("FMP_API_KEY", raising=False)
    monkeypatch.delenv("POLYGON_API_KEY", raising=False)
    monkeypatch.delenv("TIINGO_API_KEY", raising=False)
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    monkeypatch.delenv("SIMFIN_API_KEY", raising=False)
    monkeypatch.delenv("FRED_API_KEY", raising=False)

    providers = configured_providers()

    assert [provider.name for provider in providers] == ["mock"]
