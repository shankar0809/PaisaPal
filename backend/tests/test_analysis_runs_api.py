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
    assert "Mock current context for NVDA" in report["markdown_report"]
    assert "source_summary" in report["report"]
    assert any(
        item["provider"] == "mock" for item in report["report"]["source_summary"]
    )
    assert {
        item["label"] for item in report["report"]["source_summary"]
    } >= {"Mock market snapshot for NVDA"}
    assert report["report"]["data_warnings"] == ["Mock report; do not use for decisions"]


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
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setattr(routes, "configured_providers", lambda: [live_provider])
    monkeypatch.setattr(routes, "OpenAiAnalysisClient", FakeOpenAiClient)
    monkeypatch.setattr(routes, "AnalysisOrchestrator", CapturingOrchestrator)
    created = client.post("/api/analysis-runs", json={"tickers": "NVDA"}).json()

    response = client.post(f"/api/analysis-runs/{created['id']}/run")

    assert response.status_code == 200
    assert response.json()["status"] == "complete"
    assert captured["providers"] == [live_provider]
    assert isinstance(captured["ai_client"], FakeOpenAiClient)
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


def test_configured_providers_returns_alpha_vantage_when_key_is_present(monkeypatch):
    monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "demo-key")
    monkeypatch.delenv("FMP_API_KEY", raising=False)
    monkeypatch.delenv("POLYGON_API_KEY", raising=False)

    providers = configured_providers()

    assert [provider.name for provider in providers] == ["alpha_vantage"]


def test_configured_providers_falls_back_to_mock_without_provider_keys(monkeypatch):
    monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
    monkeypatch.delenv("FMP_API_KEY", raising=False)
    monkeypatch.delenv("POLYGON_API_KEY", raising=False)

    providers = configured_providers()

    assert [provider.name for provider in providers] == ["mock"]
