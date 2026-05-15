from fastapi.testclient import TestClient

from paisapal.main import app


def test_create_analysis_run_returns_jobs():
    client = TestClient(app)

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


def test_run_mock_analysis_completes_jobs_and_creates_reports():
    client = TestClient(app)
    created = client.post("/api/analysis-runs", json={"tickers": "NVDA"}).json()

    response = client.post(f"/api/analysis-runs/{created['id']}/run-mock")

    assert response.status_code == 200
    body = response.json()
    assert body["jobs"][0]["status"] == "complete"

    watchlist = client.get("/api/watchlist").json()
    nvda_rows = [row for row in watchlist if row["ticker"] == "NVDA"]
    assert nvda_rows
    assert nvda_rows[0]["final_decision"] == "Watchlist"
