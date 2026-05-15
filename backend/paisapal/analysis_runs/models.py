from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


JobStatus = Literal[
    "queued",
    "fetching_market_data",
    "fetching_fundamentals",
    "fetching_earnings",
    "fetching_options",
    "running_web_research",
    "running_gpt_analysis",
    "complete",
    "failed",
]

FinalClassification = Literal[
    "Buy / Enter",
    "Watchlist",
    "Wait for Pullback",
    "Avoid",
    "Reduce",
    "Exit",
]


class AnalysisRunSettings(BaseModel):
    account_size: float = Field(default=100000, gt=0)
    risk_percent: float = Field(default=0.5, gt=0, le=5)
    max_dollar_risk: float | None = Field(default=None, gt=0)
    notes: str = ""


class SourceSummary(BaseModel):
    provider: str
    retrieved_at: str
    status: Literal["fresh", "stale", "missing", "error"]
    label: str
    url: str | None = None
    warnings: list[str] = Field(default_factory=list)


class PositionSizingScenario(BaseModel):
    label: str
    entry: float
    stop: float
    risk_per_share: float
    shares_at_max_risk: int


class AiReportOutput(BaseModel):
    ticker: str
    company_name: str
    current_price: float
    final_classification: FinalClassification
    confidence: str
    technical_rating: str
    vcp_rating: str
    fundamental_rating: str
    earnings_rating: str
    sentiment_rating: str
    options_flow_rating: str
    risk_reward: float | None = None
    entry_zones: list[str] = Field(default_factory=list)
    stop_zones: list[str] = Field(default_factory=list)
    target_zones: list[str] = Field(default_factory=list)
    position_sizing: list[PositionSizingScenario] = Field(default_factory=list)
    bullish_factors: list[str] = Field(default_factory=list)
    bearish_risks: list[str] = Field(default_factory=list)
    data_warnings: list[str] = Field(default_factory=list)
    source_summary: list[SourceSummary] = Field(default_factory=list)
    markdown_report: str
