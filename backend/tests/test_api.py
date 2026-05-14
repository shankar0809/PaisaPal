from fastapi.testclient import TestClient

from paisapal.main import app


def test_health_endpoint():
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_import_preview_endpoint_returns_valid_rows():
    client = TestClient(app)
    csv_text = """ticker,current_price,week_52_high,week_52_low,resistance,support,ma_20,ma_50,ma_200,relative_strength,sector_trend,market_trend,entry,stop_loss,target_1,target_2
MSFT,420,430,280,425,400,415,405,360,improving,strong,supportive,420,399,462,483
"""

    response = client.post(
        "/api/import/preview",
        files={"file": ("watchlist.csv", csv_text, "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["valid_count"] == 1
