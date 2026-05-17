from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy.orm import Session

from paisapal.ai.client import build_analysis_client, is_ai_configured, selected_ai_provider
from paisapal.analysis.rules import analyze
from paisapal.analysis_runs.orchestrator import AnalysisOrchestrator, configured_providers
from paisapal.analysis_runs.source_coverage import derive_source_coverage
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
    get_latest_analysis_run_for_ticker,
    get_history,
    get_latest_report,
    get_latest_watchlist,
    list_analysis_runs,
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


@router.get("/analysis-runs", response_model=list[AnalysisRunResponse])
def analysis_runs(session: Session = Depends(get_session)) -> list[AnalysisRunResponse]:
    return [_run_response(run) for run in list_analysis_runs(session)]


@router.get("/analysis-runs/latest/{ticker}", response_model=AnalysisRunResponse)
def latest_analysis_run_for_ticker(ticker: str, session: Session = Depends(get_session)) -> AnalysisRunResponse:
    run = get_latest_analysis_run_for_ticker(session, ticker)
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
    ai_client = build_analysis_client()
    use_live_ai = ai_client is not None
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
    ai_provider = selected_ai_provider()
    ai_configured = is_ai_configured()
    market_data_mode = os.getenv("MARKET_DATA_MODE", "free").strip().lower()
    paid_fallback_enabled = os.getenv(
        "ENABLE_PAID_PROVIDER_FALLBACK",
        "false",
    ).strip().lower() in {"1", "true", "yes"}
    provider_config = {
        "polygon": bool(os.getenv("POLYGON_API_KEY")),
        "alpha_vantage": bool(os.getenv("ALPHA_VANTAGE_API_KEY")),
        "fmp": bool(os.getenv("FMP_API_KEY")),
        "tiingo": bool(os.getenv("TIINGO_API_KEY")),
        "finnhub": bool(os.getenv("FINNHUB_API_KEY")),
        "simfin": bool(os.getenv("SIMFIN_API_KEY")),
        "fred": bool(os.getenv("FRED_API_KEY")),
    }
    free_provider_config = {
        "yahoo": market_data_mode == "free",
        "sec_edgar": market_data_mode == "free",
        "stooq": market_data_mode == "free",
    }
    has_market_data = any(free_provider_config.values()) or any(provider_config.values())
    live_ready = ai_configured and has_market_data
    if live_ready:
        message = "Live AI analysis ready"
    elif not ai_configured and not has_market_data:
        message = (
            "Configure OPENAI_API_KEY and at least one market data provider"
            if ai_provider == "openai"
            else "Configure Ollama AI and at least one market data provider"
        )
    elif not ai_configured:
        message = (
            "Configure OPENAI_API_KEY for live AI commentary"
            if ai_provider == "openai"
            else "Configure Ollama AI for live commentary"
        )
    else:
        message = "Configure at least one market data provider"

    statuses = [
        ProviderStatusResponse(
            provider=ai_provider,
            configured=ai_configured,
            role="ai",
            required_for_live=True,
            live_ready=live_ready,
            message=message,
        ),
    ]
    if market_data_mode == "free":
        statuses.extend(
            [
                ProviderStatusResponse(
                    provider="yahoo",
                    configured=True,
                    role="market_data",
                    live_ready=live_ready,
                    message=message,
                ),
                ProviderStatusResponse(
                    provider="sec_edgar",
                    configured=True,
                    role="fundamentals",
                    live_ready=live_ready,
                    message=message,
                ),
                ProviderStatusResponse(
                    provider="stooq",
                    configured=free_provider_config["stooq"],
                    role="market_data",
                    live_ready=live_ready,
                    message=message,
                ),
            ]
        )
        if not paid_fallback_enabled:
            return statuses

    statuses.extend(
        [
        ProviderStatusResponse(
            provider="polygon",
            configured=provider_config["polygon"],
            role="market_data",
            live_ready=live_ready,
            message=message,
        ),
        ProviderStatusResponse(
            provider="alpha_vantage",
            configured=provider_config["alpha_vantage"],
            role="market_data",
            live_ready=live_ready,
            message=message,
        ),
        ProviderStatusResponse(
            provider="fmp",
            configured=provider_config["fmp"],
            role="fundamentals",
            live_ready=live_ready,
            message=message,
        ),
        ProviderStatusResponse(
            provider="tiingo",
            configured=provider_config["tiingo"],
            role="market_data",
            live_ready=live_ready,
            message=message,
        ),
        ProviderStatusResponse(
            provider="finnhub",
            configured=provider_config["finnhub"],
            role="market_data",
            live_ready=live_ready,
            message=message,
        ),
        ProviderStatusResponse(
            provider="simfin",
            configured=provider_config["simfin"],
            role="fundamentals",
            live_ready=live_ready,
            message=message,
        ),
        ProviderStatusResponse(
            provider="fred",
            configured=provider_config["fred"],
            role="macro",
            live_ready=live_ready,
            message=message,
        ),
        ]
    )
    return statuses


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
    report = json.loads(snapshot.report_json)
    source_coverage_input = {"source_summary": _source_summary_rows(snapshot, report)}
    return TickerReportResponse(
        ticker=snapshot.ticker,
        report=report,
        markdown_report=snapshot.markdown_report,
        created_at=snapshot.created_at.isoformat(),
        source_coverage=derive_source_coverage(source_coverage_input),
    )


def _source_summary_rows(snapshot, report: dict) -> list[dict]:
    job = getattr(snapshot, "job", None)
    sources = getattr(job, "sources", None) if job is not None else None
    if sources:
        return [
            {
                "provider": source.provider,
                "source_type": source.source_type,
                "status": source.status,
                "label": source.label,
                "url": source.url,
                "warnings": json.loads(source.warnings_json or "[]"),
            }
            for source in sources
        ]
    return report.get("source_summary", [])


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
