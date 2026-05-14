# Stock Analysis Framework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reusable stock trading and investment analysis rules engine that turns structured inputs into a consistent recommendation report.

**Architecture:** Start with a deterministic Python package and CLI before adding any UI. The core package owns typed inputs, scoring rules, position sizing, options/earnings calculations, recommendation logic, and Markdown report rendering. External market data integrations are intentionally deferred; v1 accepts user-provided JSON so the framework is testable and repeatable.

**Tech Stack:** Python 3.12, `pytest`, `ruff`, standard-library `dataclasses`, `argparse`, JSON fixtures, Markdown report output.

---

## Source Spec

Original PDF copied into the repository:

- `docs/specs/Generic_Stock_Trading_Investment_Analysis_Framework_Spec.pdf`

Key scope from the spec:

- Current stock context classification
- VCP and technical setup scoring
- Entry, target, stop-loss, risk/reward
- SEPA-style position sizing
- Last 8 earnings quality review
- Fundamental metrics scoring
- Market sentiment and crowding risk
- Options flow and implied move
- LEAP expiration and strike selection
- Earnings-specific implied move
- Directional recommendation engine
- Final report template ending in one clear decision

## File Structure

- Create: `pyproject.toml` - project metadata, dependencies, pytest/ruff config.
- Create: `README.md` - quickstart, JSON input format, CLI examples.
- Create: `src/paisapal/__init__.py` - package exports.
- Create: `src/paisapal/models.py` - typed dataclasses for every analysis area.
- Create: `src/paisapal/scoring.py` - VCP, fundamentals, sentiment, options, and earnings scoring rules.
- Create: `src/paisapal/risk.py` - risk/reward and position sizing calculations.
- Create: `src/paisapal/recommendation.py` - final directional recommendation and decision categories.
- Create: `src/paisapal/report.py` - Markdown report renderer matching the spec template.
- Create: `src/paisapal/cli.py` - `paisapal analyze input.json --account-size ...` command.
- Create: `examples/sample_analysis.json` - complete example input.
- Create: `tests/test_risk.py` - unit tests for risk and position sizing.
- Create: `tests/test_scoring.py` - unit tests for scoring rules.
- Create: `tests/test_recommendation.py` - unit tests for final decisions.
- Create: `tests/test_report.py` - unit tests for report sections.
- Create: `tests/test_cli.py` - CLI smoke test.

## Decisions For V1

- Use structured JSON input instead of live data APIs.
- Keep scoring deterministic and transparent; every score should be traceable to input fields.
- Return conservative decisions when required inputs are missing.
- Treat this as analysis tooling, not brokerage/execution software.
- Include a clear disclaimer in generated reports that output is informational, not financial advice.

---

### Task 1: Project Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/paisapal/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create project metadata**

Create `pyproject.toml`:

```toml
[project]
name = "paisapal"
version = "0.1.0"
description = "Deterministic stock trading and investment analysis framework"
requires-python = ">=3.12"
dependencies = []

[project.scripts]
paisapal = "paisapal.cli:main"

[dependency-groups]
dev = [
  "pytest>=8.0.0",
  "ruff>=0.5.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[tool.ruff]
line-length = 100
target-version = "py312"
src = ["src", "tests"]
```

- [ ] **Step 2: Create package markers**

Create `src/paisapal/__init__.py`:

```python
"""PaisaPal stock analysis framework."""

__all__ = ["__version__"]

__version__ = "0.1.0"
```

Create `tests/__init__.py` as an empty file.

- [ ] **Step 3: Create README quickstart**

Create `README.md`:

```markdown
# PaisaPal

PaisaPal is a deterministic stock trading and investment analysis framework based on the source spec in `docs/specs/`.

The first version accepts structured JSON input and generates a Markdown analysis report covering technical setup, VCP quality, earnings history, fundamentals, sentiment, options flow, LEAP setup, risk sizing, and final decision.

## Quickstart

```bash
uv sync
uv run paisapal analyze examples/sample_analysis.json --account-size 100000 --risk-percent 0.5
```

The generated analysis is informational only and is not financial advice.
```

- [ ] **Step 4: Run formatting/test baseline**

Run: `uv run pytest`

Expected: `no tests ran` or a clean pass once test files exist.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml README.md src/paisapal/__init__.py tests/__init__.py
git commit -m "chore: initialize python project"
```

---

### Task 2: Domain Models

**Files:**
- Create: `src/paisapal/models.py`
- Test: `tests/test_scoring.py`

- [ ] **Step 1: Write model import smoke test**

Create `tests/test_scoring.py`:

```python
from paisapal.models import AnalysisInput, CurrentStockContext


def test_analysis_input_can_be_constructed_with_minimum_required_fields():
    data = AnalysisInput(
        ticker="MSFT",
        current_price=420.0,
        context=CurrentStockContext(
            week_52_high=430.0,
            week_52_low=280.0,
            resistance=425.0,
            support=400.0,
            moving_average_20=415.0,
            moving_average_50=405.0,
            moving_average_200=360.0,
            relative_strength="improving",
            upcoming_catalyst="earnings in 30 days",
            sector_trend="strong",
            market_trend="supportive",
        ),
    )

    assert data.ticker == "MSFT"
    assert data.current_price == 420.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_scoring.py -v`

Expected: FAIL with `ModuleNotFoundError` or missing model names.

- [ ] **Step 3: Add dataclasses**

Create `src/paisapal/models.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CurrentStockContext:
    week_52_high: float
    week_52_low: float
    resistance: float
    support: float
    moving_average_20: float
    moving_average_50: float
    moving_average_200: float
    relative_strength: str
    upcoming_catalyst: str
    sector_trend: str
    market_trend: str


@dataclass(frozen=True)
class VcpInputs:
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


@dataclass(frozen=True)
class TradePlan:
    entry: float
    pivot: float
    stop_loss: float
    target_1: float
    target_2: float
    stretch_target: float | None = None
    entry_type: str = "pivot"


@dataclass(frozen=True)
class EarningsQuarter:
    announcement_date: str
    quarter: str
    estimated_eps: float
    actual_eps: float
    estimated_revenue: float
    actual_revenue: float
    one_day_move_percent: float
    five_day_move_percent: float


@dataclass(frozen=True)
class FundamentalScores:
    revenue_growth: int = 3
    eps_growth: int = 3
    gross_margin: int = 3
    operating_margin: int = 3
    free_cash_flow: int = 3
    balance_sheet: int = 3
    valuation: int = 3
    segment_strength: int = 3
    guidance: int = 3
    capital_return: int = 3


@dataclass(frozen=True)
class SentimentInputs:
    analyst_sentiment: str = "neutral"
    news_sentiment: str = "neutral"
    short_interest_signal: str = "neutral"
    insider_activity_signal: str = "neutral"
    sector_sentiment: str = "neutral"
    stock_rallied_sharply: bool = False
    call_heavy_options: bool = False
    valuation_elevated: bool = False
    earnings_near: bool = False


@dataclass(frozen=True)
class OptionsFlow:
    call_volume: int = 0
    put_volume: int = 0
    call_open_interest: int = 0
    put_open_interest: int = 0
    iv_rank: float | None = None
    iv_percentile: float | None = None
    expected_move: float | None = None


@dataclass(frozen=True)
class LeapCandidate:
    expiration_months: int
    strike: float
    premium: float
    delta: float
    implied_volatility: float
    open_interest: int
    bid_ask_spread_percent: float


@dataclass(frozen=True)
class EarningsImpliedMove:
    earnings_date: str
    expiration_used: str
    atm_call: float
    atm_put: float
    current_price: float


@dataclass(frozen=True)
class AnalysisInput:
    ticker: str
    current_price: float
    context: CurrentStockContext
    market_cap: str | None = None
    vcp: VcpInputs = field(default_factory=VcpInputs)
    trade_plan: TradePlan | None = None
    earnings: list[EarningsQuarter] = field(default_factory=list)
    fundamentals: FundamentalScores = field(default_factory=FundamentalScores)
    sentiment: SentimentInputs = field(default_factory=SentimentInputs)
    options_flow: OptionsFlow = field(default_factory=OptionsFlow)
    leap_candidates: list[LeapCandidate] = field(default_factory=list)
    earnings_implied_move: EarningsImpliedMove | None = None
```

- [ ] **Step 4: Run model test**

Run: `uv run pytest tests/test_scoring.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/paisapal/models.py tests/test_scoring.py
git commit -m "feat: add stock analysis domain models"
```

---

### Task 3: Risk And Position Sizing

**Files:**
- Create: `src/paisapal/risk.py`
- Test: `tests/test_risk.py`

- [ ] **Step 1: Write failing risk tests**

Create `tests/test_risk.py`:

```python
import pytest

from paisapal.risk import calculate_position_size, calculate_trade_risk


def test_calculate_trade_risk_returns_risk_reward_metrics():
    result = calculate_trade_risk(entry=100, stop_loss=92, target=116)

    assert result.risk_per_share == 8
    assert result.reward_per_share == 16
    assert result.risk_reward_ratio == 2


def test_calculate_position_size_uses_smaller_of_risk_and_portfolio_cap():
    result = calculate_position_size(
        account_size=100_000,
        risk_percent=0.5,
        entry=100,
        stop_loss=92,
        portfolio_cap_percent=10,
    )

    assert result.maximum_dollar_risk == 500
    assert result.risk_based_shares == 62
    assert result.portfolio_cap_shares == 100
    assert result.final_shares == 62


def test_calculate_trade_risk_rejects_invalid_stop():
    with pytest.raises(ValueError, match="stop_loss must be below entry"):
        calculate_trade_risk(entry=100, stop_loss=101, target=120)
```

- [ ] **Step 2: Run tests to verify failure**

Run: `uv run pytest tests/test_risk.py -v`

Expected: FAIL because `paisapal.risk` does not exist.

- [ ] **Step 3: Implement risk module**

Create `src/paisapal/risk.py`:

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TradeRisk:
    risk_per_share: float
    reward_per_share: float
    risk_reward_ratio: float


@dataclass(frozen=True)
class PositionSize:
    maximum_dollar_risk: float
    risk_based_shares: int
    portfolio_cap_shares: int
    final_shares: int


def calculate_trade_risk(entry: float, stop_loss: float, target: float) -> TradeRisk:
    if stop_loss >= entry:
        raise ValueError("stop_loss must be below entry for long trades")
    if target <= entry:
        raise ValueError("target must be above entry for long trades")

    risk_per_share = round(entry - stop_loss, 2)
    reward_per_share = round(target - entry, 2)
    risk_reward_ratio = round(reward_per_share / risk_per_share, 2)
    return TradeRisk(risk_per_share, reward_per_share, risk_reward_ratio)


def calculate_position_size(
    account_size: float,
    risk_percent: float,
    entry: float,
    stop_loss: float,
    portfolio_cap_percent: float,
) -> PositionSize:
    trade_risk = calculate_trade_risk(entry=entry, stop_loss=stop_loss, target=entry + 1)
    maximum_dollar_risk = account_size * (risk_percent / 100)
    risk_based_shares = int(maximum_dollar_risk // trade_risk.risk_per_share)
    portfolio_cap_dollars = account_size * (portfolio_cap_percent / 100)
    portfolio_cap_shares = int(portfolio_cap_dollars // entry)
    final_shares = min(risk_based_shares, portfolio_cap_shares)

    return PositionSize(
        maximum_dollar_risk=round(maximum_dollar_risk, 2),
        risk_based_shares=risk_based_shares,
        portfolio_cap_shares=portfolio_cap_shares,
        final_shares=final_shares,
    )
```

- [ ] **Step 4: Run risk tests**

Run: `uv run pytest tests/test_risk.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/paisapal/risk.py tests/test_risk.py
git commit -m "feat: add risk and position sizing"
```

---

### Task 4: Scoring Rules

**Files:**
- Create: `src/paisapal/scoring.py`
- Modify: `tests/test_scoring.py`

- [ ] **Step 1: Extend scoring tests**

Replace `tests/test_scoring.py` with:

```python
from paisapal.models import (
    AnalysisInput,
    CurrentStockContext,
    EarningsQuarter,
    FundamentalScores,
    OptionsFlow,
    SentimentInputs,
    VcpInputs,
)
from paisapal.scoring import (
    classify_fundamentals,
    classify_options_flow,
    classify_sentiment,
    score_earnings,
    score_vcp,
)


def test_analysis_input_can_be_constructed_with_minimum_required_fields():
    data = AnalysisInput(
        ticker="MSFT",
        current_price=420.0,
        context=CurrentStockContext(
            week_52_high=430.0,
            week_52_low=280.0,
            resistance=425.0,
            support=400.0,
            moving_average_20=415.0,
            moving_average_50=405.0,
            moving_average_200=360.0,
            relative_strength="improving",
            upcoming_catalyst="earnings in 30 days",
            sector_trend="strong",
            market_trend="supportive",
        ),
    )

    assert data.ticker == "MSFT"
    assert data.current_price == 420.0


def test_score_vcp_classifies_high_quality_setup():
    result = score_vcp(
        VcpInputs(
            strong_prior_uptrend=True,
            above_rising_50_day=True,
            above_rising_200_day=True,
            relative_strength_improving=True,
            orderly_consolidation=True,
            smaller_pullbacks=True,
            volume_drying_up=True,
            tightening_near_resistance=True,
            clear_pivot=True,
            strong_breakout_volume=False,
        )
    )

    assert result.score == 9
    assert result.classification == "High-quality VCP"


def test_classify_fundamentals_uses_total_score():
    result = classify_fundamentals(
        FundamentalScores(
            revenue_growth=5,
            eps_growth=5,
            gross_margin=4,
            operating_margin=4,
            free_cash_flow=5,
            balance_sheet=4,
            valuation=3,
            segment_strength=4,
            guidance=4,
            capital_return=3,
        )
    )

    assert result.score == 41
    assert result.classification == "Elite fundamentals"


def test_score_earnings_calculates_beat_rates_and_reaction():
    quarters = [
        EarningsQuarter("2026-01-30", "Q1", 1.00, 1.10, 100, 105, 3.0, 5.0),
        EarningsQuarter("2025-10-30", "Q2", 1.00, 0.90, 100, 98, -4.0, -6.0),
    ]

    result = score_earnings(quarters)

    assert result.eps_beat_rate == 0.5
    assert result.revenue_beat_rate == 0.5
    assert result.average_one_day_move == -0.5
    assert result.classification == "Mixed earnings quality"


def test_classify_sentiment_detects_crowding():
    result = classify_sentiment(
        SentimentInputs(
            analyst_sentiment="bullish",
            news_sentiment="bullish",
            stock_rallied_sharply=True,
            call_heavy_options=True,
            valuation_elevated=True,
            earnings_near=True,
        )
    )

    assert result == "Bullish but crowded"


def test_classify_options_flow_uses_put_call_ratio():
    result = classify_options_flow(OptionsFlow(call_volume=10_000, put_volume=4_000))

    assert result.put_call_volume_ratio == 0.4
    assert result.rating == "Very call-heavy / crowded"
```

- [ ] **Step 2: Run tests to verify failure**

Run: `uv run pytest tests/test_scoring.py -v`

Expected: FAIL because scoring functions do not exist.

- [ ] **Step 3: Implement scoring module**

Create `src/paisapal/scoring.py` with deterministic scoring functions for VCP, fundamentals, earnings, sentiment, and options flow. Use the exact thresholds from the spec:

```python
from __future__ import annotations

from dataclasses import dataclass

from paisapal.models import EarningsQuarter, FundamentalScores, OptionsFlow, SentimentInputs, VcpInputs


@dataclass(frozen=True)
class ScoreResult:
    score: int
    classification: str


@dataclass(frozen=True)
class EarningsScore:
    eps_beat_rate: float
    revenue_beat_rate: float
    average_one_day_move: float
    average_five_day_move: float
    positive_reaction_rate: float
    classification: str


@dataclass(frozen=True)
class OptionsFlowScore:
    put_call_volume_ratio: float | None
    put_call_open_interest_ratio: float | None
    rating: str


def score_vcp(inputs: VcpInputs) -> ScoreResult:
    checks = [
        inputs.strong_prior_uptrend,
        inputs.above_rising_50_day,
        inputs.above_rising_200_day,
        inputs.relative_strength_improving,
        inputs.orderly_consolidation,
        inputs.smaller_pullbacks,
        inputs.volume_drying_up,
        inputs.tightening_near_resistance,
        inputs.clear_pivot,
        inputs.strong_breakout_volume,
    ]
    score = sum(checks)
    if score >= 8:
        label = "High-quality VCP"
    elif score >= 5:
        label = "Watchlist candidate"
    elif score >= 3:
        label = "Weak setup"
    else:
        label = "Avoid"
    return ScoreResult(score=score, classification=label)


def classify_fundamentals(scores: FundamentalScores) -> ScoreResult:
    total = sum(scores.__dict__.values())
    if total >= 40:
        label = "Elite fundamentals"
    elif total >= 30:
        label = "Strong fundamentals"
    elif total >= 20:
        label = "Mixed fundamentals"
    elif total >= 10:
        label = "Weak fundamentals"
    else:
        label = "Avoid fundamentally"
    return ScoreResult(score=total, classification=label)


def score_earnings(quarters: list[EarningsQuarter]) -> EarningsScore:
    if not quarters:
        return EarningsScore(0, 0, 0, 0, 0, "No earnings history")

    count = len(quarters)
    eps_beat_rate = sum(q.actual_eps > q.estimated_eps for q in quarters) / count
    revenue_beat_rate = sum(q.actual_revenue > q.estimated_revenue for q in quarters) / count
    average_one_day_move = sum(q.one_day_move_percent for q in quarters) / count
    average_five_day_move = sum(q.five_day_move_percent for q in quarters) / count
    positive_reaction_rate = sum(q.one_day_move_percent > 0 for q in quarters) / count

    if eps_beat_rate >= 0.75 and revenue_beat_rate >= 0.75 and positive_reaction_rate >= 0.60:
        label = "Strong earnings momentum"
    elif eps_beat_rate < 0.50 or revenue_beat_rate < 0.50:
        label = "Weak earnings quality"
    else:
        label = "Mixed earnings quality"

    return EarningsScore(
        eps_beat_rate=round(eps_beat_rate, 2),
        revenue_beat_rate=round(revenue_beat_rate, 2),
        average_one_day_move=round(average_one_day_move, 2),
        average_five_day_move=round(average_five_day_move, 2),
        positive_reaction_rate=round(positive_reaction_rate, 2),
        classification=label,
    )


def classify_sentiment(inputs: SentimentInputs) -> str:
    crowded = (
        inputs.analyst_sentiment == "bullish"
        and inputs.stock_rallied_sharply
        and inputs.call_heavy_options
        and inputs.valuation_elevated
        and inputs.earnings_near
    )
    if crowded:
        return "Bullish but crowded"
    if inputs.analyst_sentiment == "bullish" or inputs.news_sentiment == "bullish":
        return "Bullish and improving"
    if inputs.analyst_sentiment == "bearish" and inputs.news_sentiment == "bearish":
        return "Bearish and deteriorating"
    return "Neutral"


def classify_options_flow(flow: OptionsFlow) -> OptionsFlowScore:
    volume_ratio = None if flow.call_volume == 0 else round(flow.put_volume / flow.call_volume, 2)
    oi_ratio = None if flow.call_open_interest == 0 else round(flow.put_open_interest / flow.call_open_interest, 2)

    if volume_ratio is None:
        rating = "Balanced"
    elif volume_ratio < 0.50:
        rating = "Very call-heavy / crowded"
    elif volume_ratio < 0.80:
        rating = "Bullish leaning"
    elif volume_ratio <= 1.20:
        rating = "Balanced"
    elif volume_ratio <= 1.50:
        rating = "Defensive / bearish leaning"
    else:
        rating = "Very bearish or heavy hedging"

    return OptionsFlowScore(
        put_call_volume_ratio=volume_ratio,
        put_call_open_interest_ratio=oi_ratio,
        rating=rating,
    )
```

- [ ] **Step 4: Run scoring tests**

Run: `uv run pytest tests/test_scoring.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/paisapal/scoring.py tests/test_scoring.py
git commit -m "feat: add analysis scoring rules"
```

---

### Task 5: Recommendation Engine

**Files:**
- Create: `src/paisapal/recommendation.py`
- Test: `tests/test_recommendation.py`

- [ ] **Step 1: Write failing recommendation tests**

Create `tests/test_recommendation.py`:

```python
from paisapal.recommendation import RecommendationInputs, recommend


def test_recommend_buy_for_strong_confirmed_setup():
    result = recommend(
        RecommendationInputs(
            fundamental_classification="Elite fundamentals",
            vcp_classification="High-quality VCP",
            sentiment_classification="Bullish and improving",
            options_flow_rating="Bullish leaning",
            risk_reward_ratio=2.1,
            earnings_near=False,
            stock_extended=False,
            broken_support=False,
        )
    )

    assert result.direction == "Bullish"
    assert result.preferred_strategy == "Stock / LEAP"
    assert result.final_decision == "Buy / Enter"


def test_recommend_wait_when_strong_but_extended_and_crowded():
    result = recommend(
        RecommendationInputs(
            fundamental_classification="Strong fundamentals",
            vcp_classification="High-quality VCP",
            sentiment_classification="Bullish but crowded",
            options_flow_rating="Very call-heavy / crowded",
            risk_reward_ratio=1.8,
            earnings_near=True,
            stock_extended=True,
            broken_support=False,
        )
    )

    assert result.final_decision == "Wait for Pullback"


def test_recommend_avoid_for_weak_or_poor_risk_reward():
    result = recommend(
        RecommendationInputs(
            fundamental_classification="Mixed fundamentals",
            vcp_classification="Weak setup",
            sentiment_classification="Neutral",
            options_flow_rating="Balanced",
            risk_reward_ratio=0.9,
            earnings_near=False,
            stock_extended=False,
            broken_support=False,
        )
    )

    assert result.direction == "Neutral"
    assert result.final_decision == "Avoid"
```

- [ ] **Step 2: Run tests to verify failure**

Run: `uv run pytest tests/test_recommendation.py -v`

Expected: FAIL because recommendation module does not exist.

- [ ] **Step 3: Implement recommendation module**

Create `src/paisapal/recommendation.py`:

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecommendationInputs:
    fundamental_classification: str
    vcp_classification: str
    sentiment_classification: str
    options_flow_rating: str
    risk_reward_ratio: float | None
    earnings_near: bool
    stock_extended: bool
    broken_support: bool


@dataclass(frozen=True)
class Recommendation:
    direction: str
    confidence: str
    preferred_strategy: str
    why: str
    key_risk: str
    final_decision: str


def recommend(inputs: RecommendationInputs) -> Recommendation:
    strong_fundamentals = inputs.fundamental_classification in {
        "Elite fundamentals",
        "Strong fundamentals",
    }
    strong_technical = inputs.vcp_classification == "High-quality VCP"
    acceptable_risk = inputs.risk_reward_ratio is not None and inputs.risk_reward_ratio >= 1.5
    crowded = inputs.sentiment_classification == "Bullish but crowded" or "crowded" in inputs.options_flow_rating.lower()

    if inputs.broken_support:
        return Recommendation(
            direction="Bearish",
            confidence="Medium",
            preferred_strategy="Avoid / Put spread",
            why="Support is broken and setup risk is elevated.",
            key_risk="A reclaim of support would invalidate the bearish view.",
            final_decision="Avoid",
        )

    if strong_fundamentals and strong_technical and acceptable_risk and not inputs.stock_extended and not crowded:
        return Recommendation(
            direction="Bullish",
            confidence="High",
            preferred_strategy="Stock / LEAP",
            why="Fundamentals, technical setup, and risk/reward are aligned.",
            key_risk="Break below invalidation level or deterioration in market trend.",
            final_decision="Buy / Enter",
        )

    if strong_fundamentals and strong_technical and (inputs.stock_extended or crowded or inputs.earnings_near):
        return Recommendation(
            direction="Bullish",
            confidence="Medium",
            preferred_strategy="Watchlist / Bull call spread",
            why="Business and technical quality are constructive, but timing risk is elevated.",
            key_risk="Crowded expectations or earnings volatility.",
            final_decision="Wait for Pullback",
        )

    return Recommendation(
        direction="Neutral",
        confidence="Low",
        preferred_strategy="Avoid",
        why="The setup does not meet minimum quality or risk/reward thresholds.",
        key_risk="Entering without sufficient edge.",
        final_decision="Avoid",
    )
```

- [ ] **Step 4: Run recommendation tests**

Run: `uv run pytest tests/test_recommendation.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/paisapal/recommendation.py tests/test_recommendation.py
git commit -m "feat: add final recommendation engine"
```

---

### Task 6: Report Renderer

**Files:**
- Create: `src/paisapal/report.py`
- Test: `tests/test_report.py`

- [ ] **Step 1: Write failing report test**

Create `tests/test_report.py`:

```python
from paisapal.recommendation import Recommendation
from paisapal.report import render_markdown_report


def test_render_markdown_report_includes_required_final_sections():
    report = render_markdown_report(
        ticker="MSFT",
        current_price=420.0,
        technical_setup="High-quality VCP",
        fundamental_rating="Elite fundamentals",
        sentiment_rating="Bullish and improving",
        options_flow_rating="Bullish leaning",
        risk_reward_ratio=2.0,
        recommendation=Recommendation(
            direction="Bullish",
            confidence="High",
            preferred_strategy="Stock / LEAP",
            why="Fundamentals and technicals are aligned.",
            key_risk="Break below support.",
            final_decision="Buy / Enter",
        ),
    )

    assert "# MSFT Analysis Report" in report
    assert "## Final Directional Recommendation" in report
    assert "Final Decision: Buy / Enter" in report
    assert "informational only" in report
```

- [ ] **Step 2: Run test to verify failure**

Run: `uv run pytest tests/test_report.py -v`

Expected: FAIL because report module does not exist.

- [ ] **Step 3: Implement report renderer**

Create `src/paisapal/report.py`:

```python
from __future__ import annotations

from paisapal.recommendation import Recommendation


def render_markdown_report(
    *,
    ticker: str,
    current_price: float,
    technical_setup: str,
    fundamental_rating: str,
    sentiment_rating: str,
    options_flow_rating: str,
    risk_reward_ratio: float | None,
    recommendation: Recommendation,
) -> str:
    risk_reward = "Not available" if risk_reward_ratio is None else f"{risk_reward_ratio:.2f}"
    return f"""# {ticker} Analysis Report

This report is informational only and is not financial advice.

## Current Stock Context

- Ticker: {ticker}
- Current Price: {current_price:.2f}

## Technical Setup

- VCP Status: {technical_setup}
- Risk/Reward: {risk_reward}

## Fundamental Metrics

- Fundamental Rating: {fundamental_rating}

## Market Sentiment

- Sentiment Rating: {sentiment_rating}

## Options Flow

- Options Flow Rating: {options_flow_rating}

## Final Directional Recommendation

- Direction: {recommendation.direction}
- Confidence: {recommendation.confidence}
- Preferred Strategy: {recommendation.preferred_strategy}
- Why: {recommendation.why}
- Key Risk: {recommendation.key_risk}
- Final Decision: {recommendation.final_decision}
"""
```

- [ ] **Step 4: Run report test**

Run: `uv run pytest tests/test_report.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/paisapal/report.py tests/test_report.py
git commit -m "feat: render markdown analysis report"
```

---

### Task 7: CLI And Example Input

**Files:**
- Create: `src/paisapal/cli.py`
- Create: `examples/sample_analysis.json`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing CLI test**

Create `tests/test_cli.py`:

```python
import json
import subprocess
import sys
from pathlib import Path


def test_cli_analyze_generates_report(tmp_path):
    input_file = tmp_path / "analysis.json"
    input_file.write_text(
        json.dumps(
            {
                "ticker": "MSFT",
                "current_price": 420.0,
                "context": {
                    "week_52_high": 430.0,
                    "week_52_low": 280.0,
                    "resistance": 425.0,
                    "support": 400.0,
                    "moving_average_20": 415.0,
                    "moving_average_50": 405.0,
                    "moving_average_200": 360.0,
                    "relative_strength": "improving",
                    "upcoming_catalyst": "earnings in 30 days",
                    "sector_trend": "strong",
                    "market_trend": "supportive"
                },
                "vcp": {
                    "strong_prior_uptrend": True,
                    "above_rising_50_day": True,
                    "above_rising_200_day": True,
                    "relative_strength_improving": True,
                    "orderly_consolidation": True,
                    "smaller_pullbacks": True,
                    "volume_drying_up": True,
                    "tightening_near_resistance": True,
                    "clear_pivot": True,
                    "strong_breakout_volume": False
                },
                "trade_plan": {
                    "entry": 420.0,
                    "pivot": 425.0,
                    "stop_loss": 399.0,
                    "target_1": 462.0,
                    "target_2": 483.0
                }
            }
        )
    )

    result = subprocess.run(
        [sys.executable, "-m", "paisapal.cli", "analyze", str(input_file)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "# MSFT Analysis Report" in result.stdout
    assert "Final Decision:" in result.stdout
```

- [ ] **Step 2: Run test to verify failure**

Run: `uv run pytest tests/test_cli.py -v`

Expected: FAIL because CLI module does not exist.

- [ ] **Step 3: Implement CLI**

Create `src/paisapal/cli.py` with JSON loading, dataclass construction, score calculation, recommendation, and report output.

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from paisapal.models import AnalysisInput, CurrentStockContext, TradePlan, VcpInputs
from paisapal.recommendation import RecommendationInputs, recommend
from paisapal.report import render_markdown_report
from paisapal.risk import calculate_trade_risk
from paisapal.scoring import classify_fundamentals, classify_options_flow, classify_sentiment, score_vcp


def _build_analysis_input(payload: dict[str, Any]) -> AnalysisInput:
    trade_plan = payload.get("trade_plan")
    return AnalysisInput(
        ticker=payload["ticker"],
        current_price=float(payload["current_price"]),
        context=CurrentStockContext(**payload["context"]),
        vcp=VcpInputs(**payload.get("vcp", {})),
        trade_plan=TradePlan(**trade_plan) if trade_plan else None,
    )


def analyze_file(path: Path) -> str:
    payload = json.loads(path.read_text())
    analysis = _build_analysis_input(payload)
    vcp_score = score_vcp(analysis.vcp)
    fundamentals = classify_fundamentals(analysis.fundamentals)
    sentiment = classify_sentiment(analysis.sentiment)
    options = classify_options_flow(analysis.options_flow)

    risk_reward_ratio = None
    if analysis.trade_plan:
        trade_risk = calculate_trade_risk(
            entry=analysis.trade_plan.entry,
            stop_loss=analysis.trade_plan.stop_loss,
            target=analysis.trade_plan.target_1,
        )
        risk_reward_ratio = trade_risk.risk_reward_ratio

    recommendation = recommend(
        RecommendationInputs(
            fundamental_classification=fundamentals.classification,
            vcp_classification=vcp_score.classification,
            sentiment_classification=sentiment,
            options_flow_rating=options.rating,
            risk_reward_ratio=risk_reward_ratio,
            earnings_near="earnings" in analysis.context.upcoming_catalyst.lower(),
            stock_extended=analysis.current_price > analysis.context.resistance * 1.05,
            broken_support=analysis.current_price < analysis.context.support,
        )
    )

    return render_markdown_report(
        ticker=analysis.ticker,
        current_price=analysis.current_price,
        technical_setup=vcp_score.classification,
        fundamental_rating=fundamentals.classification,
        sentiment_rating=sentiment,
        options_flow_rating=options.rating,
        risk_reward_ratio=risk_reward_ratio,
        recommendation=recommendation,
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="paisapal")
    subparsers = parser.add_subparsers(dest="command", required=True)
    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("input_file", type=Path)
    args = parser.parse_args()

    if args.command == "analyze":
        print(analyze_file(args.input_file))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Create sample input**

Create `examples/sample_analysis.json`:

```json
{
  "ticker": "MSFT",
  "current_price": 420.0,
  "context": {
    "week_52_high": 430.0,
    "week_52_low": 280.0,
    "resistance": 425.0,
    "support": 400.0,
    "moving_average_20": 415.0,
    "moving_average_50": 405.0,
    "moving_average_200": 360.0,
    "relative_strength": "improving",
    "upcoming_catalyst": "earnings in 30 days",
    "sector_trend": "strong",
    "market_trend": "supportive"
  },
  "vcp": {
    "strong_prior_uptrend": true,
    "above_rising_50_day": true,
    "above_rising_200_day": true,
    "relative_strength_improving": true,
    "orderly_consolidation": true,
    "smaller_pullbacks": true,
    "volume_drying_up": true,
    "tightening_near_resistance": true,
    "clear_pivot": true,
    "strong_breakout_volume": false
  },
  "trade_plan": {
    "entry": 420.0,
    "pivot": 425.0,
    "stop_loss": 399.0,
    "target_1": 462.0,
    "target_2": 483.0
  }
}
```

- [ ] **Step 5: Run CLI tests and sample command**

Run: `uv run pytest tests/test_cli.py -v`

Expected: PASS.

Run: `uv run paisapal analyze examples/sample_analysis.json`

Expected: Markdown report printed to stdout with `# MSFT Analysis Report` and a `Final Decision`.

- [ ] **Step 6: Commit**

```bash
git add src/paisapal/cli.py examples/sample_analysis.json tests/test_cli.py
git commit -m "feat: add analysis cli"
```

---

### Task 8: Full Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README with current capabilities**

Add sections for:

```markdown
## Current Capabilities

- VCP scoring
- Fundamental scoring
- Earnings quality scoring
- Sentiment classification
- Options flow classification
- Trade risk/reward calculation
- SEPA-style position sizing
- Final recommendation
- Markdown report generation

## Deferred

- Live market data ingestion
- Brokerage integration
- Web UI
- Authentication
- Portfolio tracking
```

- [ ] **Step 2: Run full verification**

Run: `uv run ruff check .`

Expected: PASS.

Run: `uv run pytest -v`

Expected: PASS.

Run: `uv run paisapal analyze examples/sample_analysis.json`

Expected: report prints successfully.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: document framework capabilities"
```

---

## Spec Coverage Review

- Current Stock Context: represented in `CurrentStockContext`; report includes current price and can be expanded with support/resistance.
- VCP / Technical Pattern: covered by `VcpInputs` and `score_vcp`.
- Entry, Target, Stop-Loss: covered by `TradePlan` and `calculate_trade_risk`.
- SEPA-Style Position Sizing: covered by `calculate_position_size`.
- Last 8 Earnings Review: covered by `EarningsQuarter` and `score_earnings`.
- Fundamental Metrics: covered by `FundamentalScores` and `classify_fundamentals`.
- Market Sentiment: covered by `SentimentInputs` and `classify_sentiment`.
- Options Flow / Implied Move: covered by `OptionsFlow` and `classify_options_flow`.
- LEAP Expiration / Strike Selection: modeled by `LeapCandidate`; full scoring should be a follow-up task after v1.
- Earnings-Specific Implied Move: modeled by `EarningsImpliedMove`; full scoring should be a follow-up task after v1.
- Directional Recommendation Engine: covered by `RecommendationInputs` and `recommend`.
- Generic Output Template: covered by `render_markdown_report`, initially abbreviated but structured for expansion.
- Final Decision Categories: covered by `Recommendation.final_decision`.
- Most Important Rule: enforced by requiring trade plan fields before risk/reward can be calculated.

## Follow-Up Plans After V1

- Add full LEAP scoring using expiration, delta, liquidity, IV risk, breakeven, and budget.
- Add earnings implied move scoring with ATM straddle, expected move percent, upper/lower range, and strategy selection.
- Expand report renderer to include every field from the PDF template.
- Add optional data adapters for market data providers once the deterministic engine is stable.
- Add a web UI only after the engine and report format are covered by tests.
