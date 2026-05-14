from __future__ import annotations

from pydantic import BaseModel, Field


class ContextInput(BaseModel):
    week_52_high: float
    week_52_low: float
    resistance: float
    support: float
    ma_20: float
    ma_50: float
    ma_200: float
    relative_strength: str
    sector_trend: str
    market_trend: str
    upcoming_catalyst: str = ""
    market_cap: str = ""


class TradePlan(BaseModel):
    entry: float
    stop_loss: float
    target_1: float
    target_2: float


class VcpInput(BaseModel):
    strong_prior_uptrend: bool = False
    above_rising_50_day: bool = False
    above_rising_200_day: bool = False
    relative_strength_improving: bool = False
    orderly_consolidation: bool = False
    smaller_pullbacks: bool = False
    volume_drying_up: bool = False
    tightening_near_resistance: bool = False
    clear_pivot: bool = False
    strong_breakout_volume: bool = False


class FundamentalScores(BaseModel):
    revenue_growth: int = Field(default=3, ge=1, le=5)
    eps_growth: int = Field(default=3, ge=1, le=5)
    gross_margin: int = Field(default=3, ge=1, le=5)
    operating_margin: int = Field(default=3, ge=1, le=5)
    free_cash_flow: int = Field(default=3, ge=1, le=5)
    balance_sheet: int = Field(default=3, ge=1, le=5)
    valuation: int = Field(default=3, ge=1, le=5)
    segment_strength: int = Field(default=3, ge=1, le=5)
    guidance: int = Field(default=3, ge=1, le=5)
    capital_return: int = Field(default=3, ge=1, le=5)


class SentimentInput(BaseModel):
    analyst_sentiment: str = "neutral"
    news_sentiment: str = "neutral"
    short_interest_signal: str = "neutral"
    insider_activity_signal: str = "neutral"
    sector_sentiment: str = "neutral"
    stock_rallied_sharply: bool = False
    call_heavy_options: bool = False
    valuation_elevated: bool = False
    earnings_near: bool = False


class OptionsFlow(BaseModel):
    call_volume: int = 0
    put_volume: int = 0
    call_open_interest: int = 0
    put_open_interest: int = 0
    iv_rank: float | None = None
    iv_percentile: float | None = None
    expected_move: float | None = None


class AnalysisInput(BaseModel):
    ticker: str
    current_price: float
    context: ContextInput
    trade_plan: TradePlan
    vcp: VcpInput = VcpInput()
    fundamentals: FundamentalScores = FundamentalScores()
    sentiment: SentimentInput = SentimentInput()
    options_flow: OptionsFlow = OptionsFlow()


class AnalysisResult(BaseModel):
    ticker: str
    current_price: float
    context_rating: str
    vcp_score: int
    vcp_rating: str
    fundamental_score: int
    fundamental_rating: str
    sentiment_rating: str
    options_flow_rating: str
    put_call_ratio: float | None
    risk_per_share: float | None
    risk_reward: float | None
    position_size: int | None
    confidence: str
    preferred_strategy: str
    final_decision: str
    warnings: list[str] = []
