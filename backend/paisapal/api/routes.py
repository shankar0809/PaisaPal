from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy.orm import Session

from paisapal.ai.client import OpenAiAnalysisClient
from paisapal.analysis.rules import analyze
from paisapal.analysis_runs.orchestrator import AnalysisOrchestrator, configured_providers
from paisapal.analysis_runs.validation import parse_tickers
from paisapal.api.schemas import (
    AnalysisRunCreateRequest,
    AnalysisRunResponse,
    HistoryRowResponse,
    ImportCommitResponse,
    ImportPreviewRequest,
    ImportPreviewResponse,
    ProviderStatusResponse,
    TickerReportResponse,
    WatchlistRowResponse,
)
from paisapal.csv_import.parser import ParsePreview, parse_watchlist_csv
from paisapal.db.base import SessionLocal
from paisapal.db.repository import (
    create_analysis_run,
    create_import_batch,
    get_analysis_run,
    get_history,
    get_latest_report,
    get_latest_watchlist,
    update_analysis_run_status_from_jobs,
)
from paisapal.providers.mock import MockProvider

router = APIRouter()
_PREVIEW_CACHE: dict[str, ParsePreview] = {}


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _run_response(run) -> AnalysisRunResponse:
    return AnalysisRunResponse(
        id=run.id,
        status=run.status,
        tickers=json.loads(run.tickers_json),
        account_size=run.account_size,
        risk_percent=run.risk_percent,
        max_dollar_risk=run.max_dollar_risk,
        notes=run.notes,
        created_at=run.created_at.isoformat(),
        jobs=[
            {
                "id": job.id,
                "ticker": job.ticker,
                "status": job.status,
                "error_message": job.error_message,
            }
            for job in run.jobs
        ],
    )


@router.post("/analysis-runs", response_model=AnalysisRunResponse)
def create_run(
    request: AnalysisRunCreateRequest,
    session: Session = Depends(get_session),
) -> AnalysisRunResponse:
    try:
        tickers = parse_tickers(request.tickers)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    run = create_analysis_run(
        session,
        tickers=tickers,
        account_size=request.account_size,
        risk_percent=request.risk_percent,
        max_dollar_risk=request.max_dollar_risk,
        notes=request.notes,
    )
    return _run_response(run)


@router.get("/analysis-runs/{run_id}", response_model=AnalysisRunResponse)
def analysis_run(run_id: int, session: Session = Depends(get_session)) -> AnalysisRunResponse:
    run = get_analysis_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    return _run_response(run)


@router.post("/analysis-runs/{run_id}/run-mock", response_model=AnalysisRunResponse)
def run_mock_analysis(run_id: int, session: Session = Depends(get_session)) -> AnalysisRunResponse:
    run = get_analysis_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    orchestrator = AnalysisOrchestrator(providers=[MockProvider()])
    for job in run.jobs:
        orchestrator.run_job(session, job)
    update_analysis_run_status_from_jobs(session, run_id)
    refreshed = get_analysis_run(session, run_id)
    if refreshed is None:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    return _run_response(refreshed)


@router.post("/analysis-runs/{run_id}/run", response_model=AnalysisRunResponse)
def run_analysis(run_id: int, session: Session = Depends(get_session)) -> AnalysisRunResponse:
    run = get_analysis_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    use_live_ai = bool(os.getenv("OPENAI_API_KEY"))
    ai_client = OpenAiAnalysisClient() if use_live_ai else None
    orchestrator = AnalysisOrchestrator(
        providers=configured_providers(),
        ai_client=ai_client,
        use_live_ai=use_live_ai,
    )
    for job in run.jobs:
        orchestrator.run_job(session, job)
    update_analysis_run_status_from_jobs(session, run_id)
    refreshed = get_analysis_run(session, run_id)
    if refreshed is None:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    return _run_response(refreshed)


@router.get("/provider-status", response_model=list[ProviderStatusResponse])
def provider_status() -> list[ProviderStatusResponse]:
    return [
        ProviderStatusResponse(
            provider="openai",
            configured=bool(os.getenv("OPENAI_API_KEY")),
        ),
        ProviderStatusResponse(provider="polygon", configured=bool(os.getenv("POLYGON_API_KEY"))),
        ProviderStatusResponse(
            provider="alpha_vantage",
            configured=bool(os.getenv("ALPHA_VANTAGE_API_KEY")),
        ),
        ProviderStatusResponse(provider="fmp", configured=bool(os.getenv("FMP_API_KEY"))),
    ]


@router.post("/import/preview", response_model=ImportPreviewResponse)
async def import_preview(file: UploadFile = File(...)) -> ImportPreviewResponse:
    content = await file.read()
    preview = parse_watchlist_csv(content.decode("utf-8-sig"))
    preview_id = str(uuid4())
    _PREVIEW_CACHE[preview_id] = preview
    return ImportPreviewResponse(
        preview_id=preview_id,
        valid_count=len(preview.valid_rows),
        error_count=len(preview.errors),
        warning_count=len(preview.warnings),
        errors=[error.model_dump() for error in preview.errors],
        warnings=[warning.model_dump() for warning in preview.warnings],
        rows=[
            {
                "row_number": row.row_number,
                "ticker": row.analysis_input.ticker,
                "current_price": row.analysis_input.current_price,
            }
            for row in preview.valid_rows
        ],
    )


@router.post("/import/commit", response_model=ImportCommitResponse)
def import_commit(
    request: ImportPreviewRequest,
    session: Session = Depends(get_session),
) -> ImportCommitResponse:
    preview = _PREVIEW_CACHE.get(request.preview_id)
    if preview is None:
        raise HTTPException(status_code=404, detail="Preview not found")
    batch = create_import_batch(session, "watchlist.csv", preview.valid_rows, analyze)
    return ImportCommitResponse(batch_id=batch.id, imported_count=len(preview.valid_rows))


@router.get("/watchlist", response_model=list[WatchlistRowResponse])
def watchlist(
    decision: str | None = None,
    technical: str | None = None,
    fundamentals: str | None = None,
    sentiment: str | None = None,
    sort: str = "updated_desc",
    session: Session = Depends(get_session),
) -> list[WatchlistRowResponse]:
    rows = get_latest_watchlist(
        session,
        decision=decision,
        technical=technical,
        fundamentals=fundamentals,
        sentiment=sentiment,
        sort=sort,
    )
    return [
        WatchlistRowResponse(
            id=row.id,
            ticker=row.ticker,
            current_price=row.current_price,
            final_decision=row.final_decision,
            confidence=row.confidence,
            technical_rating=row.technical_rating,
            fundamental_rating=row.fundamental_rating,
            sentiment_rating=row.sentiment_rating,
            options_flow_rating=row.options_flow_rating,
            risk_reward=row.risk_reward,
            created_at=row.created_at.isoformat(),
        )
        for row in rows
    ]


@router.get("/tickers/{ticker}", response_model=TickerReportResponse)
def ticker_report(ticker: str, session: Session = Depends(get_session)) -> TickerReportResponse:
    snapshot = get_latest_report(session, ticker)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return TickerReportResponse(
        ticker=snapshot.ticker,
        report=json.loads(snapshot.report_json),
        markdown_report=snapshot.markdown_report,
        created_at=snapshot.created_at.isoformat(),
    )


@router.get("/tickers/{ticker}/history", response_model=list[HistoryRowResponse])
def ticker_history(ticker: str, session: Session = Depends(get_session)) -> list[HistoryRowResponse]:
    rows = get_history(session, ticker)
    return [
        HistoryRowResponse(
            id=row.id,
            ticker=row.ticker,
            final_decision=row.final_decision,
            confidence=row.confidence,
            risk_reward=row.risk_reward,
            created_at=row.created_at.isoformat(),
        )
        for row in rows
    ]


@router.get("/tickers/{ticker}/report.md")
def ticker_markdown_report(ticker: str, session: Session = Depends(get_session)) -> PlainTextResponse:
    snapshot = get_latest_report(session, ticker)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return PlainTextResponse(snapshot.markdown_report)


@router.get("/sample-csv")
def sample_csv() -> FileResponse:
    path = Path(__file__).resolve().parents[3] / "examples" / "sample_watchlist.csv"
    return FileResponse(path, media_type="text/csv", filename="sample_watchlist.csv")
