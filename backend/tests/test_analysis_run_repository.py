import json
import warnings

from sqlalchemy import create_engine, select
from sqlalchemy.exc import SAWarning
from sqlalchemy.orm import sessionmaker

from paisapal.analysis.rules import analyze
from paisapal.csv_import.parser import parse_watchlist_csv
from paisapal.db.base import Base
from paisapal.db.models import AnalysisReport, SourceSnapshot
from paisapal.db.repository import (
    create_analysis_run,
    create_import_batch,
    get_analysis_run,
    get_history,
    get_latest_report,
    get_latest_watchlist,
    save_analysis_report,
)


def session_factory():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def create_csv_snapshot(session, ticker: str = "MSFT"):
    csv_text = f"""ticker,current_price,week_52_high,week_52_low,resistance,support,ma_20,ma_50,ma_200,relative_strength,sector_trend,market_trend,entry,stop_loss,target_1,target_2
{ticker},420,430,280,425,400,415,405,360,improving,strong,supportive,420,399,462,483
"""
    preview = parse_watchlist_csv(csv_text)
    create_import_batch(session, "sample.csv", preview.valid_rows, analyze)


def save_mock_report(session, ticker: str = "NVDA", price: float = 211.5):
    run = create_analysis_run(session, [ticker], 100000, 0.5, None, "")
    job = run.jobs[0]
    company_name = "NVIDIA Corporation" if ticker == "NVDA" else f"{ticker} Corporation"
    report = save_analysis_report(
        session,
        job_id=job.id,
        report={
            "ticker": ticker,
            "company_name": company_name,
            "current_price": price,
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
            "markdown_report": f"# {company_name} ({ticker}) - Stock Analysis Report",
        },
        source_snapshots=[
            {
                "provider": "mock",
                "source_type": "market",
                "status": "fresh",
                "label": "Mock market data",
                "url": None,
                "payload": {"price": price},
                "warnings": [],
            }
        ],
    )
    return job, report


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
    job, _report = save_mock_report(session)

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


def test_latest_watchlist_merges_csv_snapshots_and_ai_reports_by_ticker():
    session = session_factory()
    create_csv_snapshot(session, "MSFT")
    _job, _report = save_mock_report(session, "NVDA")

    watchlist = get_latest_watchlist(session, sort="ticker")

    assert [row.ticker for row in watchlist] == ["MSFT", "NVDA"]
    assert type(watchlist[0]).__name__ == "AnalysisSnapshot"
    assert type(watchlist[1]).__name__ == "AnalysisReport"


def test_history_combines_csv_snapshots_and_ai_reports_for_same_ticker():
    session = session_factory()
    create_csv_snapshot(session, "NVDA")
    _job, _report = save_mock_report(session, "NVDA", price=215.0)

    history = get_history(session, "nvda")

    assert [type(row).__name__ for row in history] == [
        "AnalysisReport",
        "AnalysisSnapshot",
    ]
    assert [row.ticker for row in history] == ["NVDA", "NVDA"]


def test_save_analysis_report_replaces_existing_report_for_job():
    session = session_factory()
    job, first_report = save_mock_report(session, "NVDA", price=211.5)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", SAWarning)
        save_analysis_report(
            session,
            job_id=job.id,
            report={
                "ticker": "NVDA",
                "company_name": "NVIDIA Corporation",
                "current_price": 250.0,
                "final_classification": "Buy / Enter",
                "confidence": "High",
                "technical_rating": "Breakout",
                "vcp_rating": "Actionable",
                "fundamental_rating": "Very strong",
                "earnings_rating": "Strong",
                "sentiment_rating": "Bullish",
                "options_flow_rating": "Call-heavy",
                "risk_reward": 3.0,
                "source_summary": [],
                "markdown_report": "# Updated NVIDIA Report",
            },
            source_snapshots=[
                {
                    "provider": "mock-updated",
                    "source_type": "market",
                    "status": "fresh",
                    "label": "Updated mock market data",
                    "url": None,
                    "payload": {"price": 250.0},
                    "warnings": [],
                }
            ],
        )
        session.refresh(job)
        _report = job.report

    reports = session.scalars(
        select(AnalysisReport).where(AnalysisReport.job_id == job.id)
    ).all()
    sources = session.scalars(
        select(SourceSnapshot).where(SourceSnapshot.job_id == job.id)
    ).all()

    assert [warning.category for warning in caught] == []
    assert len(reports) == 1
    assert reports[0].id == first_report.id
    assert reports[0].current_price == 250.0
    assert reports[0].final_decision == "Buy / Enter"
    assert len(sources) == 1
    assert sources[0].provider == "mock-updated"
