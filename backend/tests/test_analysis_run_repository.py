import json

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from paisapal.db.base import Base
from paisapal.db.models import SourceSnapshot
from paisapal.db.repository import (
    create_analysis_run,
    get_analysis_run,
    get_latest_report,
    get_latest_watchlist,
    save_analysis_report,
)


def session_factory():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_create_analysis_run_persists_jobs_for_each_ticker():
    session = session_factory()

    run = create_analysis_run(
        session,
        tickers=["NVDA", "TSLA"],
        account_size=100000,
        risk_percent=0.5,
        max_dollar_risk=None,
        notes="AI leaders",
    )

    loaded = get_analysis_run(session, run.id)
    assert loaded is not None
    assert loaded.status == "queued"
    assert [job.ticker for job in loaded.jobs] == ["NVDA", "TSLA"]
    assert [job.status for job in loaded.jobs] == ["queued", "queued"]


def test_save_analysis_report_feeds_watchlist_and_ticker_report():
    session = session_factory()
    run = create_analysis_run(session, ["NVDA"], 100000, 0.5, None, "")
    job = run.jobs[0]

    save_analysis_report(
        session,
        job_id=job.id,
        report={
            "ticker": "NVDA",
            "company_name": "NVIDIA Corporation",
            "current_price": 211.5,
            "final_classification": "Watchlist",
            "confidence": "Medium",
            "technical_rating": "Constructive",
            "vcp_rating": "Watchlist candidate",
            "fundamental_rating": "Very strong",
            "earnings_rating": "Strong",
            "sentiment_rating": "Bullish but crowded",
            "options_flow_rating": "Call-heavy",
            "risk_reward": 2.1,
            "source_summary": [],
            "markdown_report": "# NVIDIA Corporation (NVDA) - Stock Analysis Report",
        },
        source_snapshots=[
            {
                "provider": "mock",
                "source_type": "market",
                "status": "fresh",
                "label": "Mock market data",
                "url": None,
                "payload": {"price": 211.5},
                "warnings": [],
            }
        ],
    )

    watchlist = get_latest_watchlist(session)
    assert len(watchlist) == 1
    assert watchlist[0].ticker == "NVDA"
    assert watchlist[0].final_decision == "Watchlist"

    latest = get_latest_report(session, "nvda")
    assert latest is not None
    assert json.loads(latest.report_json)["company_name"] == "NVIDIA Corporation"

    source = session.scalar(
        select(SourceSnapshot).where(SourceSnapshot.job_id == job.id)
    )
    assert source is not None
    assert source.provider == "mock"
    assert source.source_type == "market"
    assert json.loads(source.payload_json) == {"price": 211.5}
    assert json.loads(source.warnings_json) == []
