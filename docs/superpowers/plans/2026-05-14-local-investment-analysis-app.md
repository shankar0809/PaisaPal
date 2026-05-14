# Local Investment Analysis App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local single-user FastAPI + React + SQLite app that imports CSV watchlists, runs the investment analysis framework, displays a filterable dashboard, and provides ticker drill-down reports with analysis history.

**Architecture:** The app has a pure Python analysis engine, a FastAPI backend with SQLite persistence, and a React/Vite frontend. CSV upload flows through backend validation into import batches and analysis snapshots; the frontend reads dashboard rows, ticker details, and history from JSON endpoints. The system remains local-only for v1 and has no authentication, brokerage connection, live market data dependency, or AI commentary.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, SQLite, Pydantic, pytest, httpx, ruff, Node 22+, React, TypeScript, Vite, Vitest, Testing Library, Playwright.

---

## Source Documents

- Product design: `docs/superpowers/specs/2026-05-14-local-investment-analysis-app-design.md`
- Framework PDF: `docs/specs/Generic_Stock_Trading_Investment_Analysis_Framework_Spec.pdf`
- Earlier engine-only plan: `docs/superpowers/plans/2026-05-14-stock-analysis-framework.md`

## File Structure

- Create: `pyproject.toml` - Python package, backend dependencies, test/lint config.
- Create: `README.md` - local setup, CSV format, run commands.
- Create: `.gitignore` - Python, Node, SQLite, build artifacts.
- Create: `backend/paisapal/__init__.py` - backend package marker.
- Create: `backend/paisapal/analysis/models.py` - framework input/output dataclasses.
- Create: `backend/paisapal/analysis/rules.py` - deterministic framework rules.
- Create: `backend/paisapal/analysis/report.py` - report payload builder and Markdown renderer.
- Create: `backend/paisapal/csv_import/schema.py` - accepted CSV columns and validation constants.
- Create: `backend/paisapal/csv_import/parser.py` - CSV parsing, coercion, row validation.
- Create: `backend/paisapal/db/base.py` - SQLAlchemy base and engine/session helpers.
- Create: `backend/paisapal/db/models.py` - SQLite tables for import batches, ticker inputs, snapshots.
- Create: `backend/paisapal/db/repository.py` - database write/read functions.
- Create: `backend/paisapal/api/schemas.py` - Pydantic API request/response models.
- Create: `backend/paisapal/api/routes.py` - FastAPI endpoints.
- Create: `backend/paisapal/main.py` - app factory and CORS setup.
- Create: `backend/tests/` - backend unit and API tests.
- Create: `frontend/package.json` - frontend scripts and dependencies.
- Create: `frontend/vite.config.ts` - Vite and test config.
- Create: `frontend/src/api/client.ts` - API client.
- Create: `frontend/src/types.ts` - shared frontend types.
- Create: `frontend/src/App.tsx` - route shell.
- Create: `frontend/src/pages/DashboardPage.tsx` - watchlist table.
- Create: `frontend/src/pages/ImportPage.tsx` - CSV upload and preview.
- Create: `frontend/src/pages/TickerDetailPage.tsx` - full framework report.
- Create: `frontend/src/pages/HistoryPage.tsx` - snapshot history.
- Create: `frontend/src/components/` - table, badges, report sections, upload controls.
- Create: `frontend/src/styles.css` - app styling.
- Create: `examples/sample_watchlist.csv` - importable sample data.
- Create: `scripts/dev_backend.sh` - backend local run helper.
- Create: `scripts/dev_frontend.sh` - frontend local run helper.

## Data Model

SQLite tables:

- `import_batches`: one row per CSV import attempt.
- `ticker_inputs`: normalized latest imported input per ticker and batch.
- `analysis_snapshots`: immutable calculated outputs for each imported ticker.

Each snapshot stores both structured calculated columns for dashboard filtering and a `report_json` blob for the detail page. This keeps dashboard queries simple while preserving full traceability.

## API Surface

- `GET /api/health` - backend health check.
- `POST /api/import/preview` - parse CSV and return row preview, errors, warnings.
- `POST /api/import/commit` - import valid preview rows, run analysis, save snapshots.
- `GET /api/watchlist` - latest snapshot per ticker with filter/sort query params.
- `GET /api/tickers/{ticker}` - latest full report for one ticker.
- `GET /api/tickers/{ticker}/history` - prior snapshots for one ticker.
- `GET /api/tickers/{ticker}/report.md` - latest report as Markdown.
- `GET /api/sample-csv` - sample CSV download.

---

### Task 1: Project Foundation

**Files:**
- Create: `.gitignore`
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `backend/paisapal/__init__.py`
- Create: `backend/tests/__init__.py`
- Create: `scripts/dev_backend.sh`

- [ ] **Step 1: Create `.gitignore`**

```gitignore
.DS_Store
.venv/
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
*.db
*.sqlite
node_modules/
dist/
coverage/
playwright-report/
test-results/
```

- [ ] **Step 2: Create Python project config**

Create `pyproject.toml`:

```toml
[project]
name = "paisapal"
version = "0.1.0"
description = "Local investment analysis framework app"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.115.0",
  "pydantic>=2.8.0",
  "python-multipart>=0.0.9",
  "sqlalchemy>=2.0.30",
  "uvicorn[standard]>=0.30.0"
]

[dependency-groups]
dev = [
  "httpx>=0.27.0",
  "pytest>=8.0.0",
  "pytest-cov>=5.0.0",
  "ruff>=0.5.0"
]

[tool.pytest.ini_options]
testpaths = ["backend/tests"]
pythonpath = ["backend"]

[tool.ruff]
line-length = 100
target-version = "py312"
src = ["backend"]
```

- [ ] **Step 3: Create package and test markers**

Create `backend/paisapal/__init__.py`:

```python
"""PaisaPal local investment analysis app."""

__version__ = "0.1.0"
```

Create `backend/tests/__init__.py` as an empty file.

- [ ] **Step 4: Create backend run helper**

Create `scripts/dev_backend.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
uv run uvicorn paisapal.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

Run: `chmod +x scripts/dev_backend.sh`

- [ ] **Step 5: Create README baseline**

Create `README.md`:

```markdown
# PaisaPal

PaisaPal is a local single-user investment analysis app. It imports CSV watchlists, runs a deterministic framework for technicals, fundamentals, sentiment, options flow, risk, and final decision, then displays a dashboard and ticker reports.

## Local Development

Backend:

```bash
uv sync
./scripts/dev_backend.sh
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

The app is informational only and is not financial advice.
```

- [ ] **Step 6: Verify foundation**

Run: `uv sync`

Expected: dependencies install successfully.

Run: `uv run pytest`

Expected: no tests fail.

- [ ] **Step 7: Commit**

```bash
git add .gitignore pyproject.toml README.md backend/paisapal/__init__.py backend/tests/__init__.py scripts/dev_backend.sh
git commit -m "chore: initialize local app foundation"
```

---

### Task 2: Analysis Engine

**Files:**
- Create: `backend/paisapal/analysis/models.py`
- Create: `backend/paisapal/analysis/rules.py`
- Create: `backend/paisapal/analysis/report.py`
- Create: `backend/tests/test_analysis_rules.py`

- [ ] **Step 1: Write failing analysis tests**

Create `backend/tests/test_analysis_rules.py`:

```python
from paisapal.analysis.models import AnalysisInput, ContextInput, FundamentalScores, OptionsFlow, TradePlan, VcpInput
from paisapal.analysis.rules import analyze


def strong_input() -> AnalysisInput:
    return AnalysisInput(
        ticker="MSFT",
        current_price=420,
        context=ContextInput(
            week_52_high=430,
            week_52_low=280,
            resistance=425,
            support=400,
            ma_20=415,
            ma_50=405,
            ma_200=360,
            relative_strength="improving",
            sector_trend="strong",
            market_trend="supportive",
            upcoming_catalyst="",
            market_cap="3T",
        ),
        trade_plan=TradePlan(entry=420, stop_loss=399, target_1=462, target_2=483),
        vcp=VcpInput(
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
        ),
        fundamentals=FundamentalScores(
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
        ),
        options_flow=OptionsFlow(call_volume=10000, put_volume=7000, call_open_interest=20000, put_open_interest=15000),
    )


def test_analyze_returns_buy_for_strong_setup():
    result = analyze(strong_input(), account_size=100000, risk_percent=0.5)

    assert result.ticker == "MSFT"
    assert result.vcp_score == 9
    assert result.vcp_rating == "High-quality VCP"
    assert result.fundamental_score == 41
    assert result.risk_reward == 2.0
    assert result.position_size == 23
    assert result.final_decision == "Buy / Enter"


def test_analyze_avoids_when_stop_is_invalid():
    data = strong_input()
    invalid = data.model_copy(update={"trade_plan": TradePlan(entry=420, stop_loss=430, target_1=462, target_2=483)})

    result = analyze(invalid, account_size=100000, risk_percent=0.5)

    assert result.final_decision == "Avoid"
    assert "stop_loss must be below entry" in result.warnings
```

- [ ] **Step 2: Run tests to verify failure**

Run: `uv run pytest backend/tests/test_analysis_rules.py -v`

Expected: FAIL because analysis modules do not exist.

- [ ] **Step 3: Implement analysis models**

Create `backend/paisapal/analysis/models.py` with Pydantic models:

```python
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
```

- [ ] **Step 4: Implement deterministic rules**

Create `backend/paisapal/analysis/rules.py` with pure functions:

```python
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
    if sentiment.analyst_sentiment.lower() == "bullish" or sentiment.news_sentiment.lower() == "bullish":
        return "Bullish and improving"
    if sentiment.analyst_sentiment.lower() == "bearish" and sentiment.news_sentiment.lower() == "bearish":
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
```

- [ ] **Step 5: Implement report helpers**

Create `backend/paisapal/analysis/report.py`:

```python
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
```

- [ ] **Step 6: Run analysis tests**

Run: `uv run pytest backend/tests/test_analysis_rules.py -v`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/paisapal/analysis backend/tests/test_analysis_rules.py
git commit -m "feat: add deterministic analysis engine"
```

---

### Task 3: CSV Import Parser And Validation

**Files:**
- Create: `backend/paisapal/csv_import/schema.py`
- Create: `backend/paisapal/csv_import/parser.py`
- Create: `backend/tests/test_csv_import.py`
- Create: `examples/sample_watchlist.csv`

- [ ] **Step 1: Write failing CSV tests**

Create `backend/tests/test_csv_import.py`:

```python
from paisapal.csv_import.parser import parse_watchlist_csv


def test_parse_watchlist_csv_accepts_valid_rows_and_normalizes_ticker():
    csv_text = """ticker,current_price,week_52_high,week_52_low,resistance,support,ma_20,ma_50,ma_200,relative_strength,sector_trend,market_trend,entry,stop_loss,target_1,target_2
msft,420,430,280,425,400,415,405,360,improving,strong,supportive,420,399,462,483
"""

    preview = parse_watchlist_csv(csv_text)

    assert len(preview.valid_rows) == 1
    assert preview.valid_rows[0].analysis_input.ticker == "MSFT"
    assert preview.errors == []


def test_parse_watchlist_csv_reports_invalid_stop_loss():
    csv_text = """ticker,current_price,week_52_high,week_52_low,resistance,support,ma_20,ma_50,ma_200,relative_strength,sector_trend,market_trend,entry,stop_loss,target_1,target_2
MSFT,420,430,280,425,400,415,405,360,improving,strong,supportive,420,430,462,483
"""

    preview = parse_watchlist_csv(csv_text)

    assert preview.valid_rows == []
    assert preview.errors[0].row_number == 2
    assert preview.errors[0].column == "stop_loss"
```

- [ ] **Step 2: Run tests to verify failure**

Run: `uv run pytest backend/tests/test_csv_import.py -v`

Expected: FAIL because CSV import modules do not exist.

- [ ] **Step 3: Implement CSV schema constants**

Create `backend/paisapal/csv_import/schema.py`:

```python
REQUIRED_COLUMNS = {
    "ticker",
    "current_price",
    "week_52_high",
    "week_52_low",
    "resistance",
    "support",
    "ma_20",
    "ma_50",
    "ma_200",
    "relative_strength",
    "sector_trend",
    "market_trend",
    "entry",
    "stop_loss",
    "target_1",
    "target_2",
}

BOOLEAN_COLUMNS = {
    "vcp_strong_prior_uptrend",
    "vcp_above_rising_50_day",
    "vcp_above_rising_200_day",
    "vcp_relative_strength_improving",
    "vcp_orderly_consolidation",
    "vcp_smaller_pullbacks",
    "vcp_volume_drying_up",
    "vcp_tightening_near_resistance",
    "vcp_clear_pivot",
    "vcp_strong_breakout_volume",
    "stock_rallied_sharply",
    "call_heavy_options",
    "valuation_elevated",
    "earnings_near",
}

SCORE_COLUMNS = {
    "fund_revenue_growth",
    "fund_eps_growth",
    "fund_gross_margin",
    "fund_operating_margin",
    "fund_free_cash_flow",
    "fund_balance_sheet",
    "fund_valuation",
    "fund_segment_strength",
    "fund_guidance",
    "fund_capital_return",
}
```

- [ ] **Step 4: Implement parser**

Create `backend/paisapal/csv_import/parser.py`:

```python
from __future__ import annotations

import csv
from io import StringIO

from pydantic import BaseModel

from paisapal.analysis.models import (
    AnalysisInput,
    ContextInput,
    FundamentalScores,
    OptionsFlow,
    SentimentInput,
    TradePlan,
    VcpInput,
)
from paisapal.csv_import.schema import BOOLEAN_COLUMNS, REQUIRED_COLUMNS, SCORE_COLUMNS


class CsvValidationIssue(BaseModel):
    row_number: int
    column: str
    message: str


class ValidCsvRow(BaseModel):
    row_number: int
    raw: dict[str, str]
    analysis_input: AnalysisInput


class ParsePreview(BaseModel):
    valid_rows: list[ValidCsvRow]
    errors: list[CsvValidationIssue]
    warnings: list[CsvValidationIssue]


def _parse_float(value: str, row_number: int, column: str, errors: list[CsvValidationIssue]) -> float:
    try:
        parsed = float(value)
    except ValueError:
        errors.append(CsvValidationIssue(row_number=row_number, column=column, message="must be a number"))
        return 0.0
    if parsed <= 0:
        errors.append(CsvValidationIssue(row_number=row_number, column=column, message="must be positive"))
    return parsed


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "yes", "1", "y"}


def _parse_score(value: str, row_number: int, column: str, errors: list[CsvValidationIssue]) -> int:
    if value == "":
        return 3
    try:
        parsed = int(value)
    except ValueError:
        errors.append(CsvValidationIssue(row_number=row_number, column=column, message="must be an integer from 1 to 5"))
        return 3
    if parsed < 1 or parsed > 5:
        errors.append(CsvValidationIssue(row_number=row_number, column=column, message="must be between 1 and 5"))
    return parsed


def parse_watchlist_csv(csv_text: str) -> ParsePreview:
    reader = csv.DictReader(StringIO(csv_text))
    headers = {header.strip() for header in (reader.fieldnames or [])}
    valid_rows: list[ValidCsvRow] = []
    errors: list[CsvValidationIssue] = []
    warnings: list[CsvValidationIssue] = []

    missing = REQUIRED_COLUMNS - headers
    for column in sorted(missing):
        errors.append(CsvValidationIssue(row_number=1, column=column, message="required column is missing"))

    known = REQUIRED_COLUMNS | BOOLEAN_COLUMNS | SCORE_COLUMNS | {
        "market_cap",
        "upcoming_catalyst",
        "analyst_sentiment",
        "news_sentiment",
        "short_interest_signal",
        "insider_activity_signal",
        "sector_sentiment",
        "call_volume",
        "put_volume",
        "call_open_interest",
        "put_open_interest",
        "iv_rank",
        "iv_percentile",
        "expected_move",
    }
    for column in sorted(headers - known):
        warnings.append(CsvValidationIssue(row_number=1, column=column, message="unknown column ignored"))

    if missing:
        return ParsePreview(valid_rows=[], errors=errors, warnings=warnings)

    for row_number, raw_row in enumerate(reader, start=2):
        row = {key.strip(): (value or "").strip() for key, value in raw_row.items() if key}
        row_errors: list[CsvValidationIssue] = []
        ticker = row["ticker"].upper()
        if not ticker:
            row_errors.append(CsvValidationIssue(row_number=row_number, column="ticker", message="must not be empty"))

        current_price = _parse_float(row["current_price"], row_number, "current_price", row_errors)
        entry = _parse_float(row["entry"], row_number, "entry", row_errors)
        stop_loss = _parse_float(row["stop_loss"], row_number, "stop_loss", row_errors)
        target_1 = _parse_float(row["target_1"], row_number, "target_1", row_errors)
        target_2 = _parse_float(row["target_2"], row_number, "target_2", row_errors)

        if stop_loss >= entry:
            row_errors.append(CsvValidationIssue(row_number=row_number, column="stop_loss", message="must be below entry"))
        if target_1 <= entry:
            row_errors.append(CsvValidationIssue(row_number=row_number, column="target_1", message="must be above entry"))
        if target_2 <= entry:
            row_errors.append(CsvValidationIssue(row_number=row_number, column="target_2", message="must be above entry"))

        if row_errors:
            errors.extend(row_errors)
            continue

        analysis_input = AnalysisInput(
            ticker=ticker,
            current_price=current_price,
            context=ContextInput(
                week_52_high=_parse_float(row["week_52_high"], row_number, "week_52_high", row_errors),
                week_52_low=_parse_float(row["week_52_low"], row_number, "week_52_low", row_errors),
                resistance=_parse_float(row["resistance"], row_number, "resistance", row_errors),
                support=_parse_float(row["support"], row_number, "support", row_errors),
                ma_20=_parse_float(row["ma_20"], row_number, "ma_20", row_errors),
                ma_50=_parse_float(row["ma_50"], row_number, "ma_50", row_errors),
                ma_200=_parse_float(row["ma_200"], row_number, "ma_200", row_errors),
                relative_strength=row["relative_strength"],
                sector_trend=row["sector_trend"],
                market_trend=row["market_trend"],
                upcoming_catalyst=row.get("upcoming_catalyst", ""),
                market_cap=row.get("market_cap", ""),
            ),
            trade_plan=TradePlan(entry=entry, stop_loss=stop_loss, target_1=target_1, target_2=target_2),
            vcp=VcpInput(
                strong_prior_uptrend=_parse_bool(row.get("vcp_strong_prior_uptrend", "")),
                above_rising_50_day=_parse_bool(row.get("vcp_above_rising_50_day", "")),
                above_rising_200_day=_parse_bool(row.get("vcp_above_rising_200_day", "")),
                relative_strength_improving=_parse_bool(row.get("vcp_relative_strength_improving", "")),
                orderly_consolidation=_parse_bool(row.get("vcp_orderly_consolidation", "")),
                smaller_pullbacks=_parse_bool(row.get("vcp_smaller_pullbacks", "")),
                volume_drying_up=_parse_bool(row.get("vcp_volume_drying_up", "")),
                tightening_near_resistance=_parse_bool(row.get("vcp_tightening_near_resistance", "")),
                clear_pivot=_parse_bool(row.get("vcp_clear_pivot", "")),
                strong_breakout_volume=_parse_bool(row.get("vcp_strong_breakout_volume", "")),
            ),
            fundamentals=FundamentalScores(
                revenue_growth=_parse_score(row.get("fund_revenue_growth", ""), row_number, "fund_revenue_growth", row_errors),
                eps_growth=_parse_score(row.get("fund_eps_growth", ""), row_number, "fund_eps_growth", row_errors),
                gross_margin=_parse_score(row.get("fund_gross_margin", ""), row_number, "fund_gross_margin", row_errors),
                operating_margin=_parse_score(row.get("fund_operating_margin", ""), row_number, "fund_operating_margin", row_errors),
                free_cash_flow=_parse_score(row.get("fund_free_cash_flow", ""), row_number, "fund_free_cash_flow", row_errors),
                balance_sheet=_parse_score(row.get("fund_balance_sheet", ""), row_number, "fund_balance_sheet", row_errors),
                valuation=_parse_score(row.get("fund_valuation", ""), row_number, "fund_valuation", row_errors),
                segment_strength=_parse_score(row.get("fund_segment_strength", ""), row_number, "fund_segment_strength", row_errors),
                guidance=_parse_score(row.get("fund_guidance", ""), row_number, "fund_guidance", row_errors),
                capital_return=_parse_score(row.get("fund_capital_return", ""), row_number, "fund_capital_return", row_errors),
            ),
            sentiment=SentimentInput(
                analyst_sentiment=row.get("analyst_sentiment", "neutral"),
                news_sentiment=row.get("news_sentiment", "neutral"),
                short_interest_signal=row.get("short_interest_signal", "neutral"),
                insider_activity_signal=row.get("insider_activity_signal", "neutral"),
                sector_sentiment=row.get("sector_sentiment", "neutral"),
                stock_rallied_sharply=_parse_bool(row.get("stock_rallied_sharply", "")),
                call_heavy_options=_parse_bool(row.get("call_heavy_options", "")),
                valuation_elevated=_parse_bool(row.get("valuation_elevated", "")),
                earnings_near=_parse_bool(row.get("earnings_near", "")),
            ),
            options_flow=OptionsFlow(
                call_volume=int(float(row.get("call_volume") or 0)),
                put_volume=int(float(row.get("put_volume") or 0)),
                call_open_interest=int(float(row.get("call_open_interest") or 0)),
                put_open_interest=int(float(row.get("put_open_interest") or 0)),
                iv_rank=float(row["iv_rank"]) if row.get("iv_rank") else None,
                iv_percentile=float(row["iv_percentile"]) if row.get("iv_percentile") else None,
                expected_move=float(row["expected_move"]) if row.get("expected_move") else None,
            ),
        )
        valid_rows.append(ValidCsvRow(row_number=row_number, raw=row, analysis_input=analysis_input))

    return ParsePreview(valid_rows=valid_rows, errors=errors, warnings=warnings)
```

- [ ] **Step 5: Create sample CSV**

Create `examples/sample_watchlist.csv`:

```csv
ticker,current_price,week_52_high,week_52_low,resistance,support,ma_20,ma_50,ma_200,relative_strength,sector_trend,market_trend,entry,stop_loss,target_1,target_2,vcp_strong_prior_uptrend,vcp_above_rising_50_day,vcp_above_rising_200_day,vcp_relative_strength_improving,vcp_orderly_consolidation,vcp_smaller_pullbacks,vcp_volume_drying_up,vcp_tightening_near_resistance,vcp_clear_pivot,vcp_strong_breakout_volume,fund_revenue_growth,fund_eps_growth,fund_gross_margin,fund_operating_margin,fund_free_cash_flow,fund_balance_sheet,fund_valuation,fund_segment_strength,fund_guidance,fund_capital_return,analyst_sentiment,news_sentiment,call_volume,put_volume,call_open_interest,put_open_interest
MSFT,420,430,280,425,400,415,405,360,improving,strong,supportive,420,399,462,483,true,true,true,true,true,true,true,true,true,false,5,5,4,4,5,4,3,4,4,3,bullish,bullish,10000,7000,20000,15000
NVDA,880,950,400,900,820,870,830,650,improving,strong,supportive,880,815,980,1050,true,true,true,true,true,false,true,true,true,false,5,5,5,5,5,4,2,5,4,3,bullish,bullish,25000,9000,50000,20000
```

- [ ] **Step 6: Run CSV tests**

Run: `uv run pytest backend/tests/test_csv_import.py -v`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/paisapal/csv_import backend/tests/test_csv_import.py examples/sample_watchlist.csv
git commit -m "feat: add csv import validation"
```

---

### Task 4: SQLite Persistence

**Files:**
- Create: `backend/paisapal/db/base.py`
- Create: `backend/paisapal/db/models.py`
- Create: `backend/paisapal/db/repository.py`
- Create: `backend/tests/test_repository.py`

- [ ] **Step 1: Write failing repository tests**

Create `backend/tests/test_repository.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from paisapal.analysis.rules import analyze
from paisapal.csv_import.parser import parse_watchlist_csv
from paisapal.db.base import Base
from paisapal.db.repository import create_import_batch, get_latest_watchlist


def test_create_import_batch_saves_snapshot():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    csv_text = """ticker,current_price,week_52_high,week_52_low,resistance,support,ma_20,ma_50,ma_200,relative_strength,sector_trend,market_trend,entry,stop_loss,target_1,target_2
MSFT,420,430,280,425,400,415,405,360,improving,strong,supportive,420,399,462,483
"""
    preview = parse_watchlist_csv(csv_text)
    batch = create_import_batch(session, "sample.csv", preview.valid_rows, analyze)

    rows = get_latest_watchlist(session)

    assert batch.filename == "sample.csv"
    assert rows[0].ticker == "MSFT"
    assert rows[0].final_decision in {"Watchlist", "Buy / Enter", "Avoid", "Wait for Pullback"}
```

- [ ] **Step 2: Run tests to verify failure**

Run: `uv run pytest backend/tests/test_repository.py -v`

Expected: FAIL because database modules do not exist.

- [ ] **Step 3: Implement database base**

Create `backend/paisapal/db/base.py`:

```python
from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def make_engine(db_path: str = "paisapal.sqlite"):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True) if "/" in db_path else None
    return create_engine(f"sqlite+pysqlite:///{db_path}", connect_args={"check_same_thread": False})


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
```

- [ ] **Step 4: Implement SQLAlchemy models**

Create `backend/paisapal/db/models.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paisapal.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    valid_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)

    ticker_inputs: Mapped[list[TickerInput]] = relationship(back_populates="batch")


class TickerInput(Base):
    __tablename__ = "ticker_inputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("import_batches.id"))
    ticker: Mapped[str] = mapped_column(String(20), index=True)
    input_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    batch: Mapped[ImportBatch] = relationship(back_populates="ticker_inputs")
    snapshots: Mapped[list[AnalysisSnapshot]] = relationship(back_populates="ticker_input")


class AnalysisSnapshot(Base):
    __tablename__ = "analysis_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker_input_id: Mapped[int] = mapped_column(ForeignKey("ticker_inputs.id"))
    ticker: Mapped[str] = mapped_column(String(20), index=True)
    current_price: Mapped[float] = mapped_column(Float)
    final_decision: Mapped[str] = mapped_column(String(50), index=True)
    confidence: Mapped[str] = mapped_column(String(20), index=True)
    technical_rating: Mapped[str] = mapped_column(String(80), index=True)
    fundamental_rating: Mapped[str] = mapped_column(String(80), index=True)
    sentiment_rating: Mapped[str] = mapped_column(String(80), index=True)
    options_flow_rating: Mapped[str] = mapped_column(String(80), index=True)
    risk_reward: Mapped[float | None] = mapped_column(Float, nullable=True)
    report_json: Mapped[str] = mapped_column(Text)
    markdown_report: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)

    ticker_input: Mapped[TickerInput] = relationship(back_populates="snapshots")
```

- [ ] **Step 5: Implement repository functions**

Create `backend/paisapal/db/repository.py`:

```python
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
    snapshots = session.scalars(select(AnalysisSnapshot).order_by(AnalysisSnapshot.created_at.desc())).all()
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

    statement: Select[tuple[AnalysisSnapshot]] = select(AnalysisSnapshot).where(AnalysisSnapshot.id.in_(ids))
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
```

- [ ] **Step 6: Run repository tests**

Run: `uv run pytest backend/tests/test_repository.py -v`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/paisapal/db backend/tests/test_repository.py
git commit -m "feat: add sqlite persistence"
```

---

### Task 5: FastAPI Backend

**Files:**
- Create: `backend/paisapal/api/schemas.py`
- Create: `backend/paisapal/api/routes.py`
- Create: `backend/paisapal/main.py`
- Create: `backend/tests/test_api.py`

- [ ] **Step 1: Write failing API tests**

Create `backend/tests/test_api.py`:

```python
from fastapi.testclient import TestClient

from paisapal.main import app


def test_health_endpoint():
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_import_preview_endpoint_returns_valid_rows():
    client = TestClient(app)
    csv_text = """ticker,current_price,week_52_high,week_52_low,resistance,support,ma_20,ma_50,ma_200,relative_strength,sector_trend,market_trend,entry,stop_loss,target_1,target_2
MSFT,420,430,280,425,400,415,405,360,improving,strong,supportive,420,399,462,483
"""

    response = client.post(
        "/api/import/preview",
        files={"file": ("watchlist.csv", csv_text, "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["valid_count"] == 1
```

- [ ] **Step 2: Run tests to verify failure**

Run: `uv run pytest backend/tests/test_api.py -v`

Expected: FAIL because API modules do not exist.

- [ ] **Step 3: Implement API schemas**

Create `backend/paisapal/api/schemas.py` with Pydantic response models:

- `ImportPreviewResponse`
- `ImportCommitResponse`
- `WatchlistRowResponse`
- `TickerReportResponse`
- `HistoryRowResponse`

- [ ] **Step 4: Implement API routes**

Create `backend/paisapal/api/routes.py`:

- `GET /health`
- `POST /import/preview`
- `POST /import/commit`
- `GET /watchlist`
- `GET /tickers/{ticker}`
- `GET /tickers/{ticker}/history`
- `GET /tickers/{ticker}/report.md`
- `GET /sample-csv`

Keep a module-level in-memory preview cache keyed by `preview_id` for v1. Store preview rows only until backend restart.

- [ ] **Step 5: Implement app entrypoint**

Create `backend/paisapal/main.py`:

```python
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from paisapal.api.routes import router
from paisapal.db.base import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="PaisaPal")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix="/api")
```

- [ ] **Step 6: Run API tests**

Run: `uv run pytest backend/tests/test_api.py -v`

Expected: PASS.

- [ ] **Step 7: Run backend server smoke test**

Run: `uv run uvicorn paisapal.main:app --app-dir backend --host 127.0.0.1 --port 8000`

Expected: server starts and logs `Uvicorn running on http://127.0.0.1:8000`.

Stop the server with `Ctrl-C`.

- [ ] **Step 8: Commit**

```bash
git add backend/paisapal/api backend/paisapal/main.py backend/tests/test_api.py
git commit -m "feat: add fastapi import and watchlist api"
```

---

### Task 6: Frontend Foundation

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/styles.css`
- Create: `scripts/dev_frontend.sh`

- [ ] **Step 1: Create frontend package**

Create `frontend/package.json`:

```json
{
  "scripts": {
    "dev": "vite --host 127.0.0.1",
    "build": "tsc && vite build",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "dependencies": {
    "@vitejs/plugin-react": "^5.0.0",
    "lucide-react": "^0.468.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.0.0",
    "@testing-library/react": "^16.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "jsdom": "^25.0.0",
    "typescript": "^5.6.0",
    "vite": "^7.0.0",
    "vitest": "^2.0.0"
  }
}
```

- [ ] **Step 2: Create Vite config and TypeScript config**

Create `frontend/vite.config.ts`:

```ts
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000"
    }
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts"
  }
});
```

Create `frontend/tsconfig.json` with strict TypeScript settings and `jsx` set to `react-jsx`.

- [ ] **Step 3: Create React shell**

Create `frontend/src/main.tsx`, `frontend/src/App.tsx`, and `frontend/src/styles.css`. The app shell must include:

- Left navigation for Dashboard, Import, History.
- Main content area.
- Local app title `PaisaPal`.

- [ ] **Step 4: Create frontend run helper**

Create `scripts/dev_frontend.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd frontend
npm run dev
```

Run: `chmod +x scripts/dev_frontend.sh`

- [ ] **Step 5: Install and verify frontend**

Run: `cd frontend && npm install`

Expected: dependencies install successfully.

Run: `cd frontend && npm run build`

Expected: build succeeds.

- [ ] **Step 6: Commit**

```bash
git add frontend scripts/dev_frontend.sh
git commit -m "feat: initialize react frontend"
```

---

### Task 7: Frontend API Client And Import Page

**Files:**
- Create: `frontend/src/types.ts`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/pages/ImportPage.tsx`
- Create: `frontend/src/components/CsvImportPanel.tsx`
- Create: `frontend/src/pages/ImportPage.test.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Write import page test**

Create `frontend/src/pages/ImportPage.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ImportPage } from "./ImportPage";

describe("ImportPage", () => {
  it("renders CSV upload controls", () => {
    render(<ImportPage />);

    expect(screen.getByText("CSV Import")).toBeInTheDocument();
    expect(screen.getByLabelText("Watchlist CSV")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify failure**

Run: `cd frontend && npm run test -- ImportPage.test.tsx`

Expected: FAIL because page does not exist.

- [ ] **Step 3: Add frontend types and API client**

Create `frontend/src/types.ts` with response types matching backend schemas.

Create `frontend/src/api/client.ts`:

```ts
export async function previewImport(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch("/api/import/preview", { method: "POST", body: formData });
  if (!response.ok) throw new Error("Import preview failed");
  return response.json();
}

export async function commitImport(previewId: string) {
  const response = await fetch("/api/import/commit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ preview_id: previewId })
  });
  if (!response.ok) throw new Error("Import commit failed");
  return response.json();
}
```

- [ ] **Step 4: Implement import UI**

Create `frontend/src/pages/ImportPage.tsx`:

```tsx
import { CsvImportPanel } from "../components/CsvImportPanel";

export function ImportPage() {
  return (
    <main className="page">
      <header className="pageHeader">
        <h1>CSV Import</h1>
      </header>
      <CsvImportPanel />
    </main>
  );
}
```

Create `frontend/src/components/CsvImportPanel.tsx`:

```tsx
import { ChangeEvent, useState } from "react";
import { commitImport, previewImport } from "../api/client";

export function CsvImportPanel() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<any>(null);
  const [error, setError] = useState("");

  function onFileChange(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] ?? null);
    setPreview(null);
    setError("");
  }

  async function onPreview() {
    if (!file) return;
    try {
      setPreview(await previewImport(file));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import preview failed");
    }
  }

  async function onCommit() {
    if (!preview?.preview_id) return;
    try {
      await commitImport(preview.preview_id);
      window.location.hash = "#/";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import commit failed");
    }
  }

  return (
    <section className="panel">
      <label htmlFor="watchlist-csv">Watchlist CSV</label>
      <input id="watchlist-csv" type="file" accept=".csv,text/csv" onChange={onFileChange} />
      <button type="button" onClick={onPreview} disabled={!file}>
        Preview
      </button>
      {error && <p role="alert">{error}</p>}
      {preview && (
        <div>
          <p>Valid rows: {preview.valid_count}</p>
          <button type="button" onClick={onCommit} disabled={preview.valid_count === 0}>
            Import valid rows
          </button>
        </div>
      )}
    </section>
  );
}
```

- [ ] **Step 5: Run import page test**

Run: `cd frontend && npm run test -- ImportPage.test.tsx`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/types.ts frontend/src/api frontend/src/pages/ImportPage.tsx frontend/src/components/CsvImportPanel.tsx frontend/src/pages/ImportPage.test.tsx frontend/src/App.tsx
git commit -m "feat: add csv import frontend"
```

---

### Task 8: Dashboard

**Files:**
- Create: `frontend/src/pages/DashboardPage.tsx`
- Create: `frontend/src/components/DecisionBadge.tsx`
- Create: `frontend/src/components/WatchlistTable.tsx`
- Create: `frontend/src/pages/DashboardPage.test.tsx`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Write dashboard test**

Create `frontend/src/pages/DashboardPage.test.tsx` with a mocked watchlist response and assertions for ticker, decision badge, risk/reward, and filter controls.

- [ ] **Step 2: Add API client function**

Add to `frontend/src/api/client.ts`:

```ts
export async function fetchWatchlist(params = new URLSearchParams()) {
  const query = params.toString();
  const response = await fetch(`/api/watchlist${query ? `?${query}` : ""}`);
  if (!response.ok) throw new Error("Failed to load watchlist");
  return response.json();
}
```

- [ ] **Step 3: Implement dashboard**

Dashboard must include:

- Table columns from the design.
- Filter controls for final decision, technical rating, fundamentals rating, and sentiment.
- Sort select for updated time, ticker, risk/reward, and confidence.
- Row click that opens ticker detail.

- [ ] **Step 4: Run dashboard test**

Run: `cd frontend && npm run test -- DashboardPage.test.tsx`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/DashboardPage.tsx frontend/src/components/DecisionBadge.tsx frontend/src/components/WatchlistTable.tsx frontend/src/pages/DashboardPage.test.tsx frontend/src/api/client.ts frontend/src/App.tsx
git commit -m "feat: add watchlist dashboard"
```

---

### Task 9: Ticker Detail And History

**Files:**
- Create: `frontend/src/pages/TickerDetailPage.tsx`
- Create: `frontend/src/pages/HistoryPage.tsx`
- Create: `frontend/src/components/ReportSection.tsx`
- Create: `frontend/src/pages/TickerDetailPage.test.tsx`
- Create: `frontend/src/pages/HistoryPage.test.tsx`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Write detail and history tests**

Create `frontend/src/pages/TickerDetailPage.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { TickerDetailPage } from "./TickerDetailPage";

vi.mock("../api/client", () => ({
  fetchTickerReport: async () => ({
    ticker: "MSFT",
    report: {
      input: { ticker: "MSFT", current_price: 420 },
      analysis: {
        context_rating: "Constructive consolidation",
        vcp_rating: "High-quality VCP",
        fundamental_rating: "Elite fundamentals",
        sentiment_rating: "Bullish and improving",
        options_flow_rating: "Bullish leaning",
        final_decision: "Buy / Enter"
      }
    }
  })
}));

describe("TickerDetailPage", () => {
  it("renders framework sections and final decision", async () => {
    render(<TickerDetailPage ticker="MSFT" />);

    expect(await screen.findByText("MSFT")).toBeInTheDocument();
    expect(screen.getByText("Current Stock Context")).toBeInTheDocument();
    expect(screen.getByText("Technical Setup")).toBeInTheDocument();
    expect(screen.getByText("Final Directional Recommendation")).toBeInTheDocument();
    expect(screen.getByText("Buy / Enter")).toBeInTheDocument();
  });
});
```

Create `frontend/src/pages/HistoryPage.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { HistoryPage } from "./HistoryPage";

vi.mock("../api/client", () => ({
  fetchTickerHistory: async () => [
    {
      id: 1,
      ticker: "MSFT",
      final_decision: "Buy / Enter",
      confidence: "High",
      risk_reward: 2.0,
      created_at: "2026-05-14T18:00:00Z"
    }
  ]
}));

describe("HistoryPage", () => {
  it("renders prior snapshot rows", async () => {
    render(<HistoryPage ticker="MSFT" />);

    expect(await screen.findByText("MSFT History")).toBeInTheDocument();
    expect(screen.getByText("Buy / Enter")).toBeInTheDocument();
    expect(screen.getByText("High")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Add API client functions**

Add:

```ts
export async function fetchTickerReport(ticker: string) {
  const response = await fetch(`/api/tickers/${encodeURIComponent(ticker)}`);
  if (!response.ok) throw new Error("Failed to load ticker report");
  return response.json();
}

export async function fetchTickerHistory(ticker: string) {
  const response = await fetch(`/api/tickers/${encodeURIComponent(ticker)}/history`);
  if (!response.ok) throw new Error("Failed to load ticker history");
  return response.json();
}
```

- [ ] **Step 3: Implement ticker detail**

The detail page must render:

- Current stock context
- Technical setup
- Trade plan and risk/reward
- Fundamentals
- Market sentiment
- Options flow
- LEAP analysis deferred-v1 section with explicit message `LEAP import is not enabled in v1`
- Earnings implied move deferred-v1 section with explicit message `Earnings import is not enabled in v1`
- Final directional recommendation

- [ ] **Step 4: Implement history page**

History page must show:

- Ticker selector or ticker route parameter.
- Snapshot timestamp.
- Previous final decision rows.
- Confidence and risk/reward.

- [ ] **Step 5: Run frontend tests**

Run: `cd frontend && npm run test -- TickerDetailPage.test.tsx HistoryPage.test.tsx`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/TickerDetailPage.tsx frontend/src/pages/HistoryPage.tsx frontend/src/components/ReportSection.tsx frontend/src/pages/TickerDetailPage.test.tsx frontend/src/pages/HistoryPage.test.tsx frontend/src/api/client.ts frontend/src/App.tsx
git commit -m "feat: add ticker report and history views"
```

---

### Task 10: Export, Sample CSV, And Polish

**Files:**
- Modify: `backend/paisapal/api/routes.py`
- Modify: `frontend/src/pages/ImportPage.tsx`
- Modify: `frontend/src/pages/TickerDetailPage.tsx`
- Modify: `README.md`

- [ ] **Step 1: Add sample CSV download link**

Expose `GET /api/sample-csv` from the backend and add a download link in the import page.

- [ ] **Step 2: Add Markdown report export**

Add a button in ticker detail that opens `/api/tickers/{ticker}/report.md` in a new browser tab.

- [ ] **Step 3: Add empty and error states**

Add user-facing states:

- Dashboard with no imports: `Import a CSV watchlist to start analyzing tickers.`
- Import parse failure: show backend error text.
- Missing ticker detail: `No analysis found for this ticker.`

- [ ] **Step 4: Update README**

Document:

- Backend and frontend run commands.
- CSV required columns.
- Sample CSV path.
- Local SQLite database file.
- Disclaimer.

- [ ] **Step 5: Verify polish**

Run: `uv run pytest -v`

Expected: PASS.

Run: `cd frontend && npm run test`

Expected: PASS.

Run: `cd frontend && npm run build`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/paisapal/api/routes.py frontend/src/pages/ImportPage.tsx frontend/src/pages/TickerDetailPage.tsx README.md
git commit -m "feat: add exports and local app polish"
```

---

### Task 11: End-To-End Verification

**Files:**
- Create: `frontend/e2e/import-dashboard-report.spec.ts`
- Modify: `frontend/package.json`

- [ ] **Step 1: Add Playwright**

Run: `cd frontend && npm install -D @playwright/test`

Run: `cd frontend && npx playwright install chromium`

- [ ] **Step 2: Add E2E script**

Add to `frontend/package.json`:

```json
"test:e2e": "playwright test"
```

- [ ] **Step 3: Add E2E test**

Create `frontend/e2e/import-dashboard-report.spec.ts`:

```ts
import { test, expect } from "@playwright/test";

test("imports CSV and opens ticker report", async ({ page }) => {
  await page.goto("http://127.0.0.1:5173");
  await page.getByRole("link", { name: "Import" }).click();
  await page.getByLabel("Watchlist CSV").setInputFiles("../examples/sample_watchlist.csv");
  await page.getByRole("button", { name: "Preview" }).click();
  await expect(page.getByText("Valid rows: 2")).toBeVisible();
  await page.getByRole("button", { name: "Import valid rows" }).click();
  await page.getByRole("link", { name: "Dashboard" }).click();
  await expect(page.getByText("MSFT")).toBeVisible();
  await page.getByText("MSFT").click();
  await expect(page.getByText("Final Directional Recommendation")).toBeVisible();
});
```

- [ ] **Step 4: Run full app locally**

Terminal 1:

```bash
./scripts/dev_backend.sh
```

Terminal 2:

```bash
./scripts/dev_frontend.sh
```

- [ ] **Step 5: Run E2E**

Run: `cd frontend && npm run test:e2e`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/e2e
git commit -m "test: add csv import e2e coverage"
```

---

## Final Verification

Run all checks:

```bash
uv run ruff check .
uv run pytest -v
cd frontend && npm run test
cd frontend && npm run build
```

Then run both servers and manually verify:

1. Open `http://127.0.0.1:5173`.
2. Import `examples/sample_watchlist.csv`.
3. Confirm dashboard rows appear.
4. Open `MSFT`.
5. Confirm final recommendation appears.
6. Open history for `MSFT`.
7. Export the Markdown report.

Commit final docs updates if any run instructions changed:

```bash
git add README.md
git commit -m "docs: update local app run instructions"
```

Push:

```bash
git push
```

## Spec Coverage Review

- Local-only app: covered by foundation, FastAPI, React, SQLite tasks.
- CSV import: covered by parser, API, import page, sample CSV, and E2E test.
- Watchlist/dashboard: covered by API watchlist and dashboard task.
- Drill-down report: covered by report builder, ticker API, ticker detail page.
- Analysis history: covered by immutable snapshots and history page.
- Traceable decisions: covered by `report_json`, Markdown report, and detail sections.
- Deterministic framework: covered by analysis engine tests and no external API dependency.
- No auth/live data/brokerage/AI in v1: preserved as deferred work.

## Known Follow-Up Plans

- Separate earnings-history CSV import.
- Separate LEAP-chain CSV import.
- Live market data adapters.
- Hosted deployment and user accounts.
- AI narrative generation after deterministic reports are stable.
