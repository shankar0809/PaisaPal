from __future__ import annotations

from paisapal.analysis.models import AnalysisInput, AnalysisResult


def build_report_payload(data: AnalysisInput, result: AnalysisResult) -> dict:
    return {"input": data.model_dump(), "analysis": result.model_dump()}


def render_markdown(data: AnalysisInput, result: AnalysisResult) -> str:
    return f"""# {data.ticker} Investment Analysis

This report is informational only and is not financial advice.

## Current Stock Context

- Current Price: {data.current_price}
- Context Rating: {result.context_rating}
- Support: {data.context.support}
- Resistance: {data.context.resistance}

## Technical Setup

- VCP Score: {result.vcp_score}
- VCP Rating: {result.vcp_rating}

## Trade Plan

- Entry: {data.trade_plan.entry}
- Stop-Loss: {data.trade_plan.stop_loss}
- Target 1: {data.trade_plan.target_1}
- Target 2: {data.trade_plan.target_2}
- Risk/Reward: {result.risk_reward}
- Position Size: {result.position_size}

## Fundamentals

- Fundamental Score: {result.fundamental_score}
- Fundamental Rating: {result.fundamental_rating}

## Market Sentiment

- Sentiment Rating: {result.sentiment_rating}

## Options Flow

- Options Flow Rating: {result.options_flow_rating}
- Put/Call Ratio: {result.put_call_ratio}

## Final Directional Recommendation

- Confidence: {result.confidence}
- Preferred Strategy: {result.preferred_strategy}
- Final Decision: {result.final_decision}
"""
