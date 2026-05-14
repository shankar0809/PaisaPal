from __future__ import annotations

from paisapal.analysis.models import AnalysisInput, AnalysisResult


def _vcp_score(data: AnalysisInput) -> tuple[int, str]:
    score = sum(
        [
            data.vcp.strong_prior_uptrend,
            data.vcp.above_rising_50_day,
            data.vcp.above_rising_200_day,
            data.vcp.relative_strength_improving,
            data.vcp.orderly_consolidation,
            data.vcp.smaller_pullbacks,
            data.vcp.volume_drying_up,
            data.vcp.tightening_near_resistance,
            data.vcp.clear_pivot,
            data.vcp.strong_breakout_volume,
        ]
    )
    if score >= 8:
        return score, "High-quality VCP"
    if score >= 5:
        return score, "Watchlist candidate"
    if score >= 3:
        return score, "Weak setup"
    return score, "Avoid"


def _fundamental_score(data: AnalysisInput) -> tuple[int, str]:
    total = sum(data.fundamentals.model_dump().values())
    if total >= 40:
        return total, "Elite fundamentals"
    if total >= 30:
        return total, "Strong fundamentals"
    if total >= 20:
        return total, "Mixed fundamentals"
    if total >= 10:
        return total, "Weak fundamentals"
    return total, "Avoid fundamentally"


def _sentiment_rating(data: AnalysisInput) -> str:
    sentiment = data.sentiment
    if (
        sentiment.analyst_sentiment.lower() == "bullish"
        and sentiment.stock_rallied_sharply
        and sentiment.call_heavy_options
        and sentiment.valuation_elevated
        and sentiment.earnings_near
    ):
        return "Bullish but crowded"
    if (
        sentiment.analyst_sentiment.lower() == "bullish"
        or sentiment.news_sentiment.lower() == "bullish"
    ):
        return "Bullish and improving"
    if (
        sentiment.analyst_sentiment.lower() == "bearish"
        and sentiment.news_sentiment.lower() == "bearish"
    ):
        return "Bearish and deteriorating"
    return "Neutral"


def _options_rating(data: AnalysisInput) -> tuple[str, float | None]:
    flow = data.options_flow
    ratio = None if flow.call_volume == 0 else round(flow.put_volume / flow.call_volume, 2)
    if ratio is None:
        return "Balanced", ratio
    if ratio < 0.50:
        return "Very call-heavy / crowded", ratio
    if ratio < 0.80:
        return "Bullish leaning", ratio
    if ratio <= 1.20:
        return "Balanced", ratio
    if ratio <= 1.50:
        return "Defensive / bearish leaning", ratio
    return "Very bearish or heavy hedging", ratio


def _context_rating(data: AnalysisInput) -> str:
    if data.current_price < data.context.support:
        return "Breakdown risk"
    if data.current_price > data.context.resistance and data.current_price > data.context.ma_50:
        return "Bullish continuation"
    if data.current_price >= data.context.ma_50 and data.current_price >= data.context.ma_200:
        return "Constructive consolidation"
    return "Base-building"


def analyze(data: AnalysisInput, account_size: float, risk_percent: float) -> AnalysisResult:
    warnings: list[str] = []
    vcp_score, vcp_rating = _vcp_score(data)
    fundamental_score, fundamental_rating = _fundamental_score(data)
    sentiment_rating = _sentiment_rating(data)
    options_flow_rating, put_call_ratio = _options_rating(data)
    context_rating = _context_rating(data)

    risk_per_share = None
    risk_reward = None
    position_size = None
    if data.trade_plan.stop_loss >= data.trade_plan.entry:
        warnings.append("stop_loss must be below entry")
    elif data.trade_plan.target_1 <= data.trade_plan.entry:
        warnings.append("target_1 must be above entry")
    else:
        risk_per_share = round(data.trade_plan.entry - data.trade_plan.stop_loss, 2)
        reward = round(data.trade_plan.target_1 - data.trade_plan.entry, 2)
        risk_reward = round(reward / risk_per_share, 2)
        max_dollar_risk = account_size * (risk_percent / 100)
        position_size = int(max_dollar_risk // risk_per_share)

    strong_fundamentals = fundamental_rating in {"Elite fundamentals", "Strong fundamentals"}
    strong_technicals = vcp_rating == "High-quality VCP"
    acceptable_risk = risk_reward is not None and risk_reward >= 1.5
    crowded = sentiment_rating == "Bullish but crowded" or "crowded" in options_flow_rating.lower()
    broken_support = data.current_price < data.context.support

    if warnings or broken_support or not acceptable_risk:
        decision = "Avoid"
        confidence = "Low"
        strategy = "Avoid"
    elif strong_fundamentals and strong_technicals and not crowded:
        decision = "Buy / Enter"
        confidence = "High"
        strategy = "Stock / LEAP"
    elif strong_fundamentals and strong_technicals:
        decision = "Wait for Pullback"
        confidence = "Medium"
        strategy = "Watchlist / Bull call spread"
    else:
        decision = "Watchlist"
        confidence = "Medium"
        strategy = "Watchlist"

    return AnalysisResult(
        ticker=data.ticker,
        current_price=data.current_price,
        context_rating=context_rating,
        vcp_score=vcp_score,
        vcp_rating=vcp_rating,
        fundamental_score=fundamental_score,
        fundamental_rating=fundamental_rating,
        sentiment_rating=sentiment_rating,
        options_flow_rating=options_flow_rating,
        put_call_ratio=put_call_ratio,
        risk_per_share=risk_per_share,
        risk_reward=risk_reward,
        position_size=position_size,
        confidence=confidence,
        preferred_strategy=strategy,
        final_decision=decision,
        warnings=warnings,
    )
