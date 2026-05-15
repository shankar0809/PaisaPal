from __future__ import annotations

import json
from collections.abc import Callable

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from paisapal.analysis.models import AnalysisInput, AnalysisResult
from paisapal.analysis.report import build_report_payload, render_markdown
from paisapal.csv_import.parser import ValidCsvRow
from paisapal.db.base import Base, engine
from paisapal.db.models import (
    AnalysisJob,
    AnalysisReport,
    AnalysisRun,
    AnalysisSnapshot,
    ImportBatch,
    SourceSnapshot,
    TickerInput,
)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def create_import_batch(
    session: Session,
    filename: str,
    valid_rows: list[ValidCsvRow],
    analyzer: Callable[[AnalysisInput, float, float], AnalysisResult],
) -> ImportBatch:
    batch = ImportBatch(filename=filename, valid_count=len(valid_rows), error_count=0)
    session.add(batch)
    session.flush()

    for row in valid_rows:
        analysis_input = row.analysis_input
        result = analyzer(analysis_input, 100000, 0.5)
        ticker_input = TickerInput(
            batch_id=batch.id,
            ticker=analysis_input.ticker,
            input_json=analysis_input.model_dump_json(),
        )
        session.add(ticker_input)
        session.flush()
        report_payload = build_report_payload(analysis_input, result)
        snapshot = AnalysisSnapshot(
            ticker_input_id=ticker_input.id,
            ticker=result.ticker,
            current_price=result.current_price,
            final_decision=result.final_decision,
            confidence=result.confidence,
            technical_rating=result.vcp_rating,
            fundamental_rating=result.fundamental_rating,
            sentiment_rating=result.sentiment_rating,
            options_flow_rating=result.options_flow_rating,
            risk_reward=result.risk_reward,
            report_json=json.dumps(report_payload),
            markdown_report=render_markdown(analysis_input, result),
        )
        session.add(snapshot)

    session.commit()
    session.refresh(batch)
    return batch


def _latest_snapshot_ids(session: Session) -> list[int]:
    snapshots = session.scalars(
        select(AnalysisSnapshot).order_by(AnalysisSnapshot.created_at.desc())
    ).all()
    latest: dict[str, int] = {}
    for snapshot in snapshots:
        latest.setdefault(snapshot.ticker, snapshot.id)
    return list(latest.values())


def create_analysis_run(
    session: Session,
    tickers: list[str],
    account_size: float,
    risk_percent: float,
    max_dollar_risk: float | None,
    notes: str,
) -> AnalysisRun:
    normalized_tickers = [ticker.upper() for ticker in tickers]
    run = AnalysisRun(
        tickers_json=json.dumps(normalized_tickers),
        account_size=account_size,
        risk_percent=risk_percent,
        max_dollar_risk=max_dollar_risk,
        notes=notes,
    )
    for ticker in normalized_tickers:
        run.jobs.append(AnalysisJob(ticker=ticker))

    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def get_analysis_run(session: Session, run_id: int) -> AnalysisRun | None:
    return session.get(AnalysisRun, run_id)


def update_job_status(
    session: Session,
    job_id: int,
    status: str,
    error_message: str | None = None,
) -> AnalysisJob:
    job = session.get(AnalysisJob, job_id)
    if job is None:
        raise ValueError(f"Analysis job {job_id} was not found")

    job.status = status
    job.error_message = error_message
    session.commit()
    session.refresh(job)
    return job


def save_analysis_report(
    session: Session,
    job_id: int,
    report: dict,
    source_snapshots: list[dict],
) -> AnalysisReport:
    job = session.get(AnalysisJob, job_id)
    if job is None:
        raise ValueError(f"Analysis job {job_id} was not found")

    ticker = str(report.get("ticker") or job.ticker).upper()
    source_summary = report.get("source_summary", [])
    analysis_report = session.scalar(
        select(AnalysisReport).where(AnalysisReport.job_id == job.id).limit(1)
    )
    if analysis_report is None:
        analysis_report = AnalysisReport(job_id=job.id)
        session.add(analysis_report)

    analysis_report.ticker = ticker
    analysis_report.company_name = report.get("company_name", "")
    analysis_report.current_price = report.get("current_price", 0.0)
    analysis_report.final_decision = (
        report.get("final_decision") or report.get("final_classification", "")
    )
    analysis_report.confidence = report.get("confidence", "")
    analysis_report.technical_rating = (
        report.get("technical_rating") or report.get("vcp_rating", "")
    )
    analysis_report.fundamental_rating = report.get("fundamental_rating", "")
    analysis_report.earnings_rating = report.get("earnings_rating", "")
    analysis_report.sentiment_rating = report.get("sentiment_rating", "")
    analysis_report.options_flow_rating = report.get("options_flow_rating", "")
    analysis_report.risk_reward = report.get("risk_reward")
    analysis_report.report_json = json.dumps(report)
    analysis_report.markdown_report = report.get("markdown_report", "")
    analysis_report.source_summary_json = json.dumps(source_summary)

    session.execute(delete(SourceSnapshot).where(SourceSnapshot.job_id == job.id))

    for snapshot in source_snapshots:
        session.add(
            SourceSnapshot(
                job_id=job.id,
                ticker=ticker,
                provider=snapshot.get("provider", ""),
                source_type=snapshot.get("source_type", ""),
                status=snapshot.get("status", ""),
                label=snapshot.get("label", ""),
                url=snapshot.get("url"),
                payload_json=json.dumps(snapshot.get("payload", {})),
                warnings_json=json.dumps(snapshot.get("warnings", [])),
            )
        )

    job.status = "completed"
    session.commit()
    session.refresh(analysis_report)
    return analysis_report


def _latest_report_ids(session: Session) -> list[int]:
    reports = session.scalars(
        select(AnalysisReport).order_by(AnalysisReport.created_at.desc())
    ).all()
    latest: dict[str, int] = {}
    for report in reports:
        latest.setdefault(report.ticker, report.id)
    return list(latest.values())


def _filter_analysis_rows(
    rows: list[AnalysisReport | AnalysisSnapshot],
    decision: str | None = None,
    technical: str | None = None,
    fundamentals: str | None = None,
    sentiment: str | None = None,
) -> list[AnalysisReport | AnalysisSnapshot]:
    if decision:
        rows = [row for row in rows if row.final_decision == decision]
    if technical:
        rows = [row for row in rows if row.technical_rating == technical]
    if fundamentals:
        rows = [row for row in rows if row.fundamental_rating == fundamentals]
    if sentiment:
        rows = [row for row in rows if row.sentiment_rating == sentiment]
    return rows


def _sort_analysis_rows(
    rows: list[AnalysisReport | AnalysisSnapshot],
    sort: str,
) -> list[AnalysisReport | AnalysisSnapshot]:
    if sort == "ticker":
        return sorted(rows, key=lambda row: row.ticker)
    if sort == "risk_reward":
        return sorted(
            rows,
            key=lambda row: (
                row.risk_reward is None,
                -(row.risk_reward or 0),
            ),
        )
    if sort == "confidence":
        return sorted(rows, key=lambda row: row.confidence)
    return sorted(rows, key=lambda row: row.created_at, reverse=True)


def get_latest_watchlist(
    session: Session,
    decision: str | None = None,
    technical: str | None = None,
    fundamentals: str | None = None,
    sentiment: str | None = None,
    sort: str = "updated_desc",
) -> list[AnalysisReport | AnalysisSnapshot]:
    report_ids = _latest_report_ids(session)
    reports = list(
        session.scalars(select(AnalysisReport).where(AnalysisReport.id.in_(report_ids)))
        .all()
        if report_ids
        else []
    )
    report_tickers = {report.ticker for report in reports}

    snapshot_ids = _latest_snapshot_ids(session)
    snapshots = list(
        session.scalars(
            select(AnalysisSnapshot).where(AnalysisSnapshot.id.in_(snapshot_ids))
        ).all()
        if snapshot_ids
        else []
    )

    rows: list[AnalysisReport | AnalysisSnapshot] = [
        snapshot for snapshot in snapshots if snapshot.ticker not in report_tickers
    ]
    rows.extend(reports)
    rows = _filter_analysis_rows(rows, decision, technical, fundamentals, sentiment)
    return _sort_analysis_rows(rows, sort)


def get_latest_report(
    session: Session,
    ticker: str,
) -> AnalysisReport | AnalysisSnapshot | None:
    normalized_ticker = ticker.upper()
    report = session.scalar(
        select(AnalysisReport)
        .where(AnalysisReport.ticker == normalized_ticker)
        .order_by(AnalysisReport.created_at.desc())
        .limit(1)
    )
    if report is not None:
        return report

    return session.scalar(
        select(AnalysisSnapshot)
        .where(AnalysisSnapshot.ticker == normalized_ticker)
        .order_by(AnalysisSnapshot.created_at.desc())
        .limit(1)
    )


def get_history(session: Session, ticker: str) -> list[AnalysisReport | AnalysisSnapshot]:
    normalized_ticker = ticker.upper()
    reports = list(
        session.scalars(
            select(AnalysisReport)
            .where(AnalysisReport.ticker == normalized_ticker)
            .order_by(AnalysisReport.created_at.desc())
        ).all()
    )
    snapshots = list(
        session.scalars(
            select(AnalysisSnapshot)
            .where(AnalysisSnapshot.ticker == normalized_ticker)
            .order_by(AnalysisSnapshot.created_at.desc())
        ).all()
    )
    rows: list[AnalysisReport | AnalysisSnapshot] = [*reports, *snapshots]
    return _sort_analysis_rows(rows, "updated_desc")
