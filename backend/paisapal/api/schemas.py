from __future__ import annotations

from pydantic import BaseModel


class ImportPreviewRequest(BaseModel):
    preview_id: str


class CsvIssueResponse(BaseModel):
    row_number: int
    column: str
    message: str


class ImportPreviewResponse(BaseModel):
    preview_id: str
    valid_count: int
    error_count: int
    warning_count: int
    errors: list[CsvIssueResponse]
    warnings: list[CsvIssueResponse]
    rows: list[dict]


class ImportCommitResponse(BaseModel):
    batch_id: int
    imported_count: int


class WatchlistRowResponse(BaseModel):
    id: int
    ticker: str
    current_price: float
    final_decision: str
    confidence: str
    technical_rating: str
    fundamental_rating: str
    sentiment_rating: str
    options_flow_rating: str
    risk_reward: float | None
    created_at: str


class TickerReportResponse(BaseModel):
    ticker: str
    report: dict
    markdown_report: str
    created_at: str


class HistoryRowResponse(BaseModel):
    id: int
    ticker: str
    final_decision: str
    confidence: str
    risk_reward: float | None
    created_at: str
