from __future__ import annotations

import json
from collections.abc import Callable

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from paisapal.analysis.models import AnalysisInput, AnalysisResult
from paisapal.analysis.report import build_report_payload, render_markdown
from paisapal.csv_import.parser import ValidCsvRow
from paisapal.db.base import Base, engine
from paisapal.db.models import AnalysisSnapshot, ImportBatch, TickerInput


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


def get_latest_watchlist(
    session: Session,
    decision: str | None = None,
    technical: str | None = None,
    fundamentals: str | None = None,
    sentiment: str | None = None,
    sort: str = "updated_desc",
) -> list[AnalysisSnapshot]:
    ids = _latest_snapshot_ids(session)
    if not ids:
        return []

    statement: Select[tuple[AnalysisSnapshot]] = select(AnalysisSnapshot).where(
        AnalysisSnapshot.id.in_(ids)
    )
    if decision:
        statement = statement.where(AnalysisSnapshot.final_decision == decision)
    if technical:
        statement = statement.where(AnalysisSnapshot.technical_rating == technical)
    if fundamentals:
        statement = statement.where(AnalysisSnapshot.fundamental_rating == fundamentals)
    if sentiment:
        statement = statement.where(AnalysisSnapshot.sentiment_rating == sentiment)

    if sort == "ticker":
        statement = statement.order_by(AnalysisSnapshot.ticker.asc())
    elif sort == "risk_reward":
        statement = statement.order_by(AnalysisSnapshot.risk_reward.desc().nullslast())
    elif sort == "confidence":
        statement = statement.order_by(AnalysisSnapshot.confidence.asc())
    else:
        statement = statement.order_by(AnalysisSnapshot.created_at.desc())

    return list(session.scalars(statement).all())


def get_latest_report(session: Session, ticker: str) -> AnalysisSnapshot | None:
    return session.scalar(
        select(AnalysisSnapshot)
        .where(AnalysisSnapshot.ticker == ticker.upper())
        .order_by(AnalysisSnapshot.created_at.desc())
        .limit(1)
    )


def get_history(session: Session, ticker: str) -> list[AnalysisSnapshot]:
    return list(
        session.scalars(
            select(AnalysisSnapshot)
            .where(AnalysisSnapshot.ticker == ticker.upper())
            .order_by(AnalysisSnapshot.created_at.desc())
        ).all()
    )
