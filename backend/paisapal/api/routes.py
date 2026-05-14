from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy.orm import Session

from paisapal.analysis.rules import analyze
from paisapal.api.schemas import (
    HistoryRowResponse,
    ImportCommitResponse,
    ImportPreviewRequest,
    ImportPreviewResponse,
    TickerReportResponse,
    WatchlistRowResponse,
)
from paisapal.csv_import.parser import ParsePreview, parse_watchlist_csv
from paisapal.db.base import SessionLocal
from paisapal.db.repository import (
    create_import_batch,
    get_history,
    get_latest_report,
    get_latest_watchlist,
)

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
