import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from paisapal.api.routes import get_session
from paisapal.db.base import Base
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
    assert report["report"]["source_summary"][0]["provider"] == "mock"
    assert report["report"]["data_warnings"] == ["Mock report; do not use for decisions"]
