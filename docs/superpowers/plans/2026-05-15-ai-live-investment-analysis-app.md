# AI Live Investment Analysis App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the CSV-first PaisaPal workflow with ticker-based analysis runs that gather live/provider evidence, use GPT-5.5 plus web research, and generate structured dashboard summaries and detailed investment reports.

**Architecture:** Keep the existing FastAPI + SQLite + React/Vite app, but add an analysis-run orchestration layer. Start with mocked provider and GPT outputs so persistence and UI can be tested deterministically, then add provider adapters, OpenAI analysis, and web-research evidence behind environment-variable configuration.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, Pydantic, pytest, httpx, React, TypeScript, Vite, Vitest, Testing Library, OpenAI Responses API, Polygon, Alpha Vantage, Financial Modeling Prep.

---

## Source Documents

- Product spec: `docs/superpowers/specs/2026-05-15-ai-live-investment-analysis-app-design.md`
- Existing framework PDF: `docs/specs/Generic_Stock_Trading_Investment_Analysis_Framework_Spec.pdf`
- Current CSV-first design for historical context: `docs/superpowers/specs/2026-05-14-local-investment-analysis-app-design.md`

## File Structure

- Modify: `pyproject.toml` - add OpenAI/http client/runtime dependencies when GPT/provider adapters are introduced.
- Modify: `README.md` - replace CSV-first workflow docs with ticker-analysis setup and environment variables.
- Create: `backend/paisapal/analysis_runs/models.py` - Pydantic domain models for run settings, job status, evidence snapshots, and AI report output.
- Create: `backend/paisapal/analysis_runs/validation.py` - ticker parsing and symbol validation.
- Create: `backend/paisapal/analysis_runs/mock_pipeline.py` - deterministic mocked analysis pipeline used by early API/UI tests.
- Create: `backend/paisapal/analysis_runs/orchestrator.py` - coordinates provider fetching, GPT analysis, status transitions, retries, and persistence.
- Create: `backend/paisapal/providers/base.py` - provider adapter protocols and normalized evidence models.
- Create: `backend/paisapal/providers/mock.py` - deterministic provider adapter for tests and local keyless development.
- Create: `backend/paisapal/providers/alpha_vantage.py` - Alpha Vantage adapter.
- Create: `backend/paisapal/providers/fmp.py` - Financial Modeling Prep adapter.
- Create: `backend/paisapal/providers/polygon.py` - Polygon adapter.
- Create: `backend/paisapal/ai/client.py` - OpenAI Responses API wrapper.
- Create: `backend/paisapal/ai/prompts.py` - framework/report prompt assembly.
- Create: `backend/paisapal/ai/schemas.py` - structured GPT output schema and validation helpers.
- Modify: `backend/paisapal/db/models.py` - add `AnalysisRun`, `AnalysisJob`, `SourceSnapshot`, and `AnalysisReport`; keep existing CSV tables until UI migration is stable.
- Modify: `backend/paisapal/db/repository.py` - add run/job/source/report persistence and update watchlist/history queries to read AI reports.
- Modify: `backend/paisapal/api/schemas.py` - add request/response schemas for analysis runs, jobs, provider status, and AI report fields.
- Modify: `backend/paisapal/api/routes.py` - add analysis-run endpoints, provider-status endpoint, and report export endpoints; leave CSV endpoints temporarily.
- Create: `backend/tests/test_analysis_run_validation.py` - ticker parsing tests.
- Create: `backend/tests/test_analysis_runs_api.py` - run creation/status/report API tests.
- Create: `backend/tests/test_provider_adapters.py` - normalization and missing-data tests.
- Create: `backend/tests/test_ai_output_validation.py` - structured-output validation tests.
- Modify: `frontend/src/types.ts` - add analysis run, job, source summary, and expanded report types.
- Modify: `frontend/src/api/client.ts` - add analysis run and provider-status client functions.
- Modify: `frontend/src/App.tsx` - replace Import nav with Analyze nav.
- Create: `frontend/src/pages/AnalyzePage.tsx` - ticker input and risk settings screen.
- Create: `frontend/src/pages/RunProgressPage.tsx` - per-ticker job progress screen.
- Modify: `frontend/src/pages/DashboardPage.tsx` - update filters and table fields for AI reports.
- Modify: `frontend/src/pages/TickerDetailPage.tsx` - render full Markdown report and source/freshness details.
- Modify: `frontend/src/components/WatchlistTable.tsx` - add AI report columns.
- Create: `frontend/src/components/TickerInputPanel.tsx` - ticker/risk form component.
- Create: `frontend/src/components/JobStatusTable.tsx` - run-progress table component.
- Create: `frontend/src/components/SourceSummary.tsx` - source/freshness display.
- Create: `frontend/src/pages/AnalyzePage.test.tsx` - form validation and submit tests.
- Create: `frontend/src/pages/RunProgressPage.test.tsx` - job status rendering tests.
- Modify: `frontend/src/pages/DashboardPage.test.tsx` - AI report dashboard fields.
- Modify: `frontend/src/pages/TickerDetailPage.test.tsx` - Markdown/source display.

## Data Model

New SQLite tables:

- `analysis_runs`: user-triggered ticker batch, account size, risk settings, optional notes, run status.
- `analysis_jobs`: one ticker per run with status, error text, stage timestamps, and retry count.
- `source_snapshots`: provider/web evidence stored per job and source.
- `analysis_reports`: validated GPT output, full Markdown report, dashboard fields, and source summary.

Existing CSV tables remain during migration. Once ticker analysis is fully verified, remove CSV navigation first, then remove CSV endpoints/tables in a cleanup task.

## Status Values

Use exact job statuses:

```python
JOB_STATUSES = [
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
```

Use exact final classifications:

```python
FINAL_CLASSIFICATIONS = [
    "Buy / Enter",
    "Watchlist",
    "Wait for Pullback",
    "Avoid",
    "Reduce",
    "Exit",
]
```

---

### Task 1: Ticker Parsing and Analysis-Run Domain Models

**Files:**
- Create: `backend/paisapal/analysis_runs/__init__.py`
- Create: `backend/paisapal/analysis_runs/models.py`
- Create: `backend/paisapal/analysis_runs/validation.py`
- Create: `backend/tests/test_analysis_run_validation.py`

- [ ] **Step 1: Write failing ticker validation tests**

Create `backend/tests/test_analysis_run_validation.py`:

```python
import pytest

from paisapal.analysis_runs.validation import parse_tickers


def test_parse_tickers_accepts_commas_lines_and_spaces():
    assert parse_tickers(" nvda, tsla\ncoin  ") == ["NVDA", "TSLA", "COIN"]


def test_parse_tickers_removes_duplicates_preserving_order():
    assert parse_tickers("NVDA, tsla, nvda, TSLA, hood") == ["NVDA", "TSLA", "HOOD"]


def test_parse_tickers_rejects_malformed_symbols():
    with pytest.raises(ValueError, match="Invalid ticker: BRK/B"):
        parse_tickers("NVDA, BRK/B")


def test_parse_tickers_rejects_empty_input():
    with pytest.raises(ValueError, match="Enter at least one ticker"):
        parse_tickers(" , \n ")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m pytest backend/tests/test_analysis_run_validation.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'paisapal.analysis_runs'`.

- [ ] **Step 3: Add domain models**

Create `backend/paisapal/analysis_runs/__init__.py`:

```python
"""Ticker-driven analysis run orchestration."""
```

Create `backend/paisapal/analysis_runs/models.py`:

```python
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
```

- [ ] **Step 4: Add ticker parsing**

Create `backend/paisapal/analysis_runs/validation.py`:

```python
from __future__ import annotations

import re

_TICKER_PATTERN = re.compile(r"^[A-Z][A-Z0-9.-]{0,9}$")


def parse_tickers(raw: str) -> list[str]:
    candidates = [value.strip().upper() for value in re.split(r"[\s,]+", raw) if value.strip()]
    if not candidates:
        raise ValueError("Enter at least one ticker")

    tickers: list[str] = []
    seen: set[str] = set()
    for ticker in candidates:
        if not _TICKER_PATTERN.fullmatch(ticker):
            raise ValueError(f"Invalid ticker: {ticker}")
        if ticker not in seen:
            tickers.append(ticker)
            seen.add(ticker)
    return tickers
```

- [ ] **Step 5: Run the validation tests**

Run: `python3 -m pytest backend/tests/test_analysis_run_validation.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/paisapal/analysis_runs backend/tests/test_analysis_run_validation.py
git commit -m "feat: add ticker analysis run domain models"
```

---

### Task 2: Persistence for Analysis Runs, Jobs, Sources, and Reports

**Files:**
- Modify: `backend/paisapal/db/models.py`
- Modify: `backend/paisapal/db/repository.py`
- Create: `backend/tests/test_analysis_run_repository.py`

- [ ] **Step 1: Write failing repository tests**

Create `backend/tests/test_analysis_run_repository.py`:

```python
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from paisapal.db.base import Base
from paisapal.db.repository import (
    create_analysis_run,
    get_analysis_run,
    get_latest_report,
    get_latest_watchlist,
    save_analysis_report,
)


def session_factory():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_create_analysis_run_persists_jobs_for_each_ticker():
    session = session_factory()

    run = create_analysis_run(
        session,
        tickers=["NVDA", "TSLA"],
        account_size=100000,
        risk_percent=0.5,
        max_dollar_risk=None,
        notes="AI leaders",
    )

    loaded = get_analysis_run(session, run.id)
    assert loaded is not None
    assert loaded.status == "queued"
    assert [job.ticker for job in loaded.jobs] == ["NVDA", "TSLA"]
    assert [job.status for job in loaded.jobs] == ["queued", "queued"]


def test_save_analysis_report_feeds_watchlist_and_ticker_report():
    session = session_factory()
    run = create_analysis_run(session, ["NVDA"], 100000, 0.5, None, "")
    job = run.jobs[0]

    save_analysis_report(
        session,
        job_id=job.id,
        report={
            "ticker": "NVDA",
            "company_name": "NVIDIA Corporation",
            "current_price": 211.5,
            "final_classification": "Watchlist",
            "confidence": "Medium",
            "technical_rating": "Constructive",
            "vcp_rating": "Watchlist candidate",
            "fundamental_rating": "Very strong",
            "earnings_rating": "Strong",
            "sentiment_rating": "Bullish but crowded",
            "options_flow_rating": "Call-heavy",
            "risk_reward": 2.1,
            "source_summary": [],
            "markdown_report": "# NVIDIA Corporation (NVDA) - Stock Analysis Report",
        },
        source_snapshots=[
            {
                "provider": "mock",
                "source_type": "market",
                "status": "fresh",
                "label": "Mock market data",
                "url": None,
                "payload": {"price": 211.5},
                "warnings": [],
            }
        ],
    )

    watchlist = get_latest_watchlist(session)
    assert len(watchlist) == 1
    assert watchlist[0].ticker == "NVDA"
    assert watchlist[0].final_decision == "Watchlist"

    latest = get_latest_report(session, "nvda")
    assert latest is not None
    assert json.loads(latest.report_json)["company_name"] == "NVIDIA Corporation"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m pytest backend/tests/test_analysis_run_repository.py -v`

Expected: FAIL with missing repository functions or missing model classes.

- [ ] **Step 3: Add database models**

Modify `backend/paisapal/db/models.py` by adding these classes below `AnalysisSnapshot`:

```python
class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tickers_json: Mapped[str] = mapped_column(Text)
    account_size: Mapped[float] = mapped_column(Float)
    risk_percent: Mapped[float] = mapped_column(Float)
    max_dollar_risk: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    jobs: Mapped[list[AnalysisJob]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="AnalysisJob.id",
    )


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("analysis_runs.id"), index=True)
    ticker: Mapped[str] = mapped_column(String(20), index=True)
    status: Mapped[str] = mapped_column(String(40), default="queued", index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    run: Mapped[AnalysisRun] = relationship(back_populates="jobs")
    sources: Mapped[list[SourceSnapshot]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )
    report: Mapped[AnalysisReport | None] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )


class SourceSnapshot(Base):
    __tablename__ = "source_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("analysis_jobs.id"), index=True)
    ticker: Mapped[str] = mapped_column(String(20), index=True)
    provider: Mapped[str] = mapped_column(String(80), index=True)
    source_type: Mapped[str] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    label: Mapped[str] = mapped_column(String(255))
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload_json: Mapped[str] = mapped_column(Text)
    warnings_json: Mapped[str] = mapped_column(Text, default="[]")
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    job: Mapped[AnalysisJob] = relationship(back_populates="sources")


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("analysis_jobs.id"), index=True)
    ticker: Mapped[str] = mapped_column(String(20), index=True)
    company_name: Mapped[str] = mapped_column(String(255))
    current_price: Mapped[float] = mapped_column(Float)
    final_decision: Mapped[str] = mapped_column(String(50), index=True)
    confidence: Mapped[str] = mapped_column(String(30), index=True)
    technical_rating: Mapped[str] = mapped_column(String(80), index=True)
    fundamental_rating: Mapped[str] = mapped_column(String(80), index=True)
    earnings_rating: Mapped[str] = mapped_column(String(80), index=True)
    sentiment_rating: Mapped[str] = mapped_column(String(80), index=True)
    options_flow_rating: Mapped[str] = mapped_column(String(80), index=True)
    risk_reward: Mapped[float | None] = mapped_column(Float, nullable=True)
    report_json: Mapped[str] = mapped_column(Text)
    markdown_report: Mapped[str] = mapped_column(Text)
    source_summary_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)

    job: Mapped[AnalysisJob] = relationship(back_populates="report")
```

- [ ] **Step 4: Add repository functions**

Modify imports in `backend/paisapal/db/repository.py`:

```python
from paisapal.db.models import (
    AnalysisJob,
    AnalysisReport,
    AnalysisRun,
    AnalysisSnapshot,
    ImportBatch,
    SourceSnapshot,
    TickerInput,
)
```

Add these functions above `_latest_snapshot_ids`:

```python
def create_analysis_run(
    session: Session,
    tickers: list[str],
    account_size: float,
    risk_percent: float,
    max_dollar_risk: float | None,
    notes: str,
) -> AnalysisRun:
    run = AnalysisRun(
        tickers_json=json.dumps(tickers),
        account_size=account_size,
        risk_percent=risk_percent,
        max_dollar_risk=max_dollar_risk,
        notes=notes,
        status="queued",
    )
    session.add(run)
    session.flush()
    for ticker in tickers:
        session.add(AnalysisJob(run_id=run.id, ticker=ticker, status="queued"))
    session.commit()
    session.refresh(run)
    return run


def get_analysis_run(session: Session, run_id: int) -> AnalysisRun | None:
    return session.get(AnalysisRun, run_id)


def update_job_status(
    session: Session,
    job_id: int,
    status: str,
    error_message: str | None = None,
) -> AnalysisJob:
    job = session.get(AnalysisJob, job_id)
    if job is None:
        raise ValueError(f"Analysis job not found: {job_id}")
    job.status = status
    job.error_message = error_message
    session.commit()
    session.refresh(job)
    return job


def save_analysis_report(
    session: Session,
    job_id: int,
    report: dict,
    source_snapshots: list[dict],
) -> AnalysisReport:
    job = session.get(AnalysisJob, job_id)
    if job is None:
        raise ValueError(f"Analysis job not found: {job_id}")

    for source in source_snapshots:
        session.add(
            SourceSnapshot(
                job_id=job.id,
                ticker=job.ticker,
                provider=source["provider"],
                source_type=source["source_type"],
                status=source["status"],
                label=source["label"],
                url=source.get("url"),
                payload_json=json.dumps(source.get("payload", {})),
                warnings_json=json.dumps(source.get("warnings", [])),
            )
        )

    saved = AnalysisReport(
        job_id=job.id,
        ticker=report["ticker"].upper(),
        company_name=report["company_name"],
        current_price=report["current_price"],
        final_decision=report["final_classification"],
        confidence=report["confidence"],
        technical_rating=report["technical_rating"],
        fundamental_rating=report["fundamental_rating"],
        earnings_rating=report["earnings_rating"],
        sentiment_rating=report["sentiment_rating"],
        options_flow_rating=report["options_flow_rating"],
        risk_reward=report.get("risk_reward"),
        report_json=json.dumps(report),
        markdown_report=report["markdown_report"],
        source_summary_json=json.dumps(report.get("source_summary", [])),
    )
    job.status = "complete"
    session.add(saved)
    session.commit()
    session.refresh(saved)
    return saved
```

- [ ] **Step 5: Update latest watchlist/report queries to prefer AI reports**

Modify `_latest_snapshot_ids`, `get_latest_watchlist`, `get_latest_report`, and `get_history` by adding AI-report branches:

```python
def _latest_report_ids(session: Session) -> list[int]:
    reports = session.scalars(select(AnalysisReport).order_by(AnalysisReport.created_at.desc())).all()
    latest: dict[str, int] = {}
    for report in reports:
        latest.setdefault(report.ticker, report.id)
    return list(latest.values())
```

At the start of `get_latest_watchlist`, before reading `AnalysisSnapshot`, add:

```python
    report_ids = _latest_report_ids(session)
    if report_ids:
        statement: Select[tuple[AnalysisReport]] = select(AnalysisReport).where(
            AnalysisReport.id.in_(report_ids)
        )
        if decision:
            statement = statement.where(AnalysisReport.final_decision == decision)
        if technical:
            statement = statement.where(AnalysisReport.technical_rating == technical)
        if fundamentals:
            statement = statement.where(AnalysisReport.fundamental_rating == fundamentals)
        if sentiment:
            statement = statement.where(AnalysisReport.sentiment_rating == sentiment)
        if sort == "ticker":
            statement = statement.order_by(AnalysisReport.ticker.asc())
        elif sort == "risk_reward":
            statement = statement.order_by(AnalysisReport.risk_reward.desc().nullslast())
        elif sort == "confidence":
            statement = statement.order_by(AnalysisReport.confidence.asc())
        else:
            statement = statement.order_by(AnalysisReport.created_at.desc())
        return list(session.scalars(statement).all())
```

At the start of `get_latest_report`, add:

```python
    ai_report = session.scalar(
        select(AnalysisReport)
        .where(AnalysisReport.ticker == ticker.upper())
        .order_by(AnalysisReport.created_at.desc())
        .limit(1)
    )
    if ai_report is not None:
        return ai_report
```

At the start of `get_history`, add:

```python
    ai_reports = list(
        session.scalars(
            select(AnalysisReport)
            .where(AnalysisReport.ticker == ticker.upper())
            .order_by(AnalysisReport.created_at.desc())
        ).all()
    )
    if ai_reports:
        return ai_reports
```

- [ ] **Step 6: Run repository tests**

Run: `python3 -m pytest backend/tests/test_analysis_run_repository.py -v`

Expected: PASS.

- [ ] **Step 7: Run existing backend tests**

Run: `python3 -m pytest backend/tests -v`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/paisapal/db/models.py backend/paisapal/db/repository.py backend/tests/test_analysis_run_repository.py
git commit -m "feat: persist ticker analysis runs and reports"
```

---

### Task 3: Mock Analysis-Run API

**Files:**
- Create: `backend/paisapal/analysis_runs/mock_pipeline.py`
- Modify: `backend/paisapal/api/schemas.py`
- Modify: `backend/paisapal/api/routes.py`
- Create: `backend/tests/test_analysis_runs_api.py`

- [ ] **Step 1: Write failing API tests**

Create `backend/tests/test_analysis_runs_api.py`:

```python
from fastapi.testclient import TestClient

from paisapal.main import app


def test_create_analysis_run_returns_jobs():
    client = TestClient(app)

    response = client.post(
        "/api/analysis-runs",
        json={
            "tickers": "NVDA, TSLA",
            "account_size": 100000,
            "risk_percent": 0.5,
            "notes": "AI leaders",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "queued"
    assert [job["ticker"] for job in body["jobs"]] == ["NVDA", "TSLA"]
    assert [job["status"] for job in body["jobs"]] == ["queued", "queued"]


def test_run_mock_analysis_completes_jobs_and_creates_reports():
    client = TestClient(app)
    created = client.post("/api/analysis-runs", json={"tickers": "NVDA"}).json()

    response = client.post(f"/api/analysis-runs/{created['id']}/run-mock")

    assert response.status_code == 200
    body = response.json()
    assert body["jobs"][0]["status"] == "complete"

    watchlist = client.get("/api/watchlist").json()
    assert watchlist[0]["ticker"] == "NVDA"
    assert watchlist[0]["final_decision"] == "Watchlist"
```

- [ ] **Step 2: Run the API tests to verify they fail**

Run: `python3 -m pytest backend/tests/test_analysis_runs_api.py -v`

Expected: FAIL with `404 Not Found` for `/api/analysis-runs`.

- [ ] **Step 3: Add API schemas**

Append to `backend/paisapal/api/schemas.py`:

```python
class AnalysisRunCreateRequest(BaseModel):
    tickers: str
    account_size: float = 100000
    risk_percent: float = 0.5
    max_dollar_risk: float | None = None
    notes: str = ""


class AnalysisJobResponse(BaseModel):
    id: int
    ticker: str
    status: str
    error_message: str | None = None


class AnalysisRunResponse(BaseModel):
    id: int
    status: str
    tickers: list[str]
    account_size: float
    risk_percent: float
    max_dollar_risk: float | None
    notes: str
    created_at: str
    jobs: list[AnalysisJobResponse]


class ProviderStatusResponse(BaseModel):
    provider: str
    configured: bool
```

- [ ] **Step 4: Add mock pipeline**

Create `backend/paisapal/analysis_runs/mock_pipeline.py`:

```python
from __future__ import annotations


def build_mock_report(ticker: str) -> dict:
    company = {
        "NVDA": "NVIDIA Corporation",
        "TSLA": "Tesla",
        "COIN": "Coinbase Global",
        "HOOD": "Robinhood Markets",
        "INTC": "Intel Corporation",
        "MU": "Micron Technology",
    }.get(ticker, f"{ticker} Corporation")
    markdown = f"""# {company} ({ticker}) - Stock Analysis Report

## 1. Current Stock Context

Mock current context for {ticker}. This generated report verifies the ticker-run workflow before live providers and GPT are connected.

## 2. VCP / Technical Pattern View

Watchlist candidate. Breakout confirmation is required.

## 3. Entry, Stop-Loss, and Target Zones

Preferred setup: wait for a confirmed breakout or a controlled pullback.

## 4. SEPA-Style Position Sizing

Use 0.25%-0.5% account risk for this mocked setup.

## 5. Earnings Review

Earnings evidence is mocked in this phase.

## 6. Fundamental Metrics

Fundamental evidence is mocked in this phase.

## 7. Market Sentiment

Sentiment evidence is mocked in this phase.

## 8. Options Flow / Implied Move

Options evidence is mocked in this phase.

## 9. Final View

{ticker} classification: Watchlist.
"""
    return {
        "ticker": ticker,
        "company_name": company,
        "current_price": 100.0,
        "final_classification": "Watchlist",
        "confidence": "Low",
        "technical_rating": "Mock constructive",
        "vcp_rating": "Watchlist candidate",
        "fundamental_rating": "Mock incomplete",
        "earnings_rating": "Mock incomplete",
        "sentiment_rating": "Mock incomplete",
        "options_flow_rating": "Mock incomplete",
        "risk_reward": 2.0,
        "entry_zones": ["Breakout above resistance", "Pullback to support"],
        "stop_zones": ["Below recent support"],
        "target_zones": ["Target 1", "Target 2"],
        "position_sizing": [],
        "bullish_factors": ["Ticker-run workflow verified"],
        "bearish_risks": ["Live data not connected in mock phase"],
        "data_warnings": ["Mock report; do not use for decisions"],
        "source_summary": [
            {
                "provider": "mock",
                "retrieved_at": "mock",
                "status": "fresh",
                "label": "Mock source",
                "url": None,
                "warnings": ["Mock data"],
            }
        ],
        "markdown_report": markdown,
    }


def build_mock_sources(ticker: str) -> list[dict]:
    return [
        {
            "provider": "mock",
            "source_type": "market",
            "status": "fresh",
            "label": f"Mock market data for {ticker}",
            "url": None,
            "payload": {"ticker": ticker, "price": 100.0},
            "warnings": ["Mock source used before live adapters are connected"],
        }
    ]
```

- [ ] **Step 5: Add routes**

Modify imports in `backend/paisapal/api/routes.py`:

```python
import os

from paisapal.analysis_runs.mock_pipeline import build_mock_report, build_mock_sources
from paisapal.analysis_runs.validation import parse_tickers
```

Add schemas to the existing import list:

```python
    AnalysisRunCreateRequest,
    AnalysisRunResponse,
    ProviderStatusResponse,
```

Add repository functions to the existing import list:

```python
    create_analysis_run,
    get_analysis_run,
    save_analysis_report,
```

Add helpers and endpoints below `health`:

```python
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
    for job in run.jobs:
        save_analysis_report(
            session,
            job_id=job.id,
            report=build_mock_report(job.ticker),
            source_snapshots=build_mock_sources(job.ticker),
        )
    refreshed = get_analysis_run(session, run_id)
    if refreshed is None:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    return _run_response(refreshed)


@router.get("/provider-status", response_model=list[ProviderStatusResponse])
def provider_status() -> list[ProviderStatusResponse]:
    return [
        ProviderStatusResponse(provider="openai", configured=bool(os.getenv("OPENAI_API_KEY"))),
        ProviderStatusResponse(provider="polygon", configured=bool(os.getenv("POLYGON_API_KEY"))),
        ProviderStatusResponse(provider="alpha_vantage", configured=bool(os.getenv("ALPHA_VANTAGE_API_KEY"))),
        ProviderStatusResponse(provider="fmp", configured=bool(os.getenv("FMP_API_KEY"))),
    ]
```

- [ ] **Step 6: Run API tests**

Run: `python3 -m pytest backend/tests/test_analysis_runs_api.py -v`

Expected: PASS.

- [ ] **Step 7: Run backend suite**

Run: `python3 -m pytest backend/tests -v`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/paisapal/analysis_runs/mock_pipeline.py backend/paisapal/api/schemas.py backend/paisapal/api/routes.py backend/tests/test_analysis_runs_api.py
git commit -m "feat: add mock ticker analysis run API"
```

---

### Task 4: Analyze Screen and Run Progress UI

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/App.tsx`
- Create: `frontend/src/components/TickerInputPanel.tsx`
- Create: `frontend/src/components/JobStatusTable.tsx`
- Create: `frontend/src/pages/AnalyzePage.tsx`
- Create: `frontend/src/pages/RunProgressPage.tsx`
- Create: `frontend/src/pages/AnalyzePage.test.tsx`
- Create: `frontend/src/pages/RunProgressPage.test.tsx`

- [ ] **Step 1: Add frontend types**

Append to `frontend/src/types.ts`:

```ts
export type AnalysisJob = {
  id: number;
  ticker: string;
  status: string;
  error_message: string | null;
};

export type AnalysisRun = {
  id: number;
  status: string;
  tickers: string[];
  account_size: number;
  risk_percent: number;
  max_dollar_risk: number | null;
  notes: string;
  created_at: string;
  jobs: AnalysisJob[];
};

export type ProviderStatus = {
  provider: string;
  configured: boolean;
};
```

- [ ] **Step 2: Add API client functions**

Modify `frontend/src/api/client.ts` import:

```ts
import type {
  AnalysisRun,
  HistoryRow,
  ImportCommit,
  ImportPreview,
  ProviderStatus,
  TickerReport,
  WatchlistRow
} from "../types";
```

Append:

```ts
export async function createAnalysisRun(payload: {
  tickers: string;
  account_size: number;
  risk_percent: number;
  max_dollar_risk?: number | null;
  notes?: string;
}): Promise<AnalysisRun> {
  const response = await fetch("/api/analysis-runs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) throw new Error("Failed to create analysis run");
  return response.json();
}

export async function fetchAnalysisRun(runId: number): Promise<AnalysisRun> {
  const response = await fetch(`/api/analysis-runs/${runId}`);
  if (!response.ok) throw new Error("Failed to load analysis run");
  return response.json();
}

export async function runMockAnalysis(runId: number): Promise<AnalysisRun> {
  const response = await fetch(`/api/analysis-runs/${runId}/run-mock`, { method: "POST" });
  if (!response.ok) throw new Error("Failed to run mock analysis");
  return response.json();
}

export async function fetchProviderStatus(): Promise<ProviderStatus[]> {
  const response = await fetch("/api/provider-status");
  if (!response.ok) throw new Error("Failed to load provider status");
  return response.json();
}
```

- [ ] **Step 3: Create ticker input component**

Create `frontend/src/components/TickerInputPanel.tsx`:

```tsx
import { Play } from "lucide-react";
import { FormEvent, useState } from "react";

type TickerInputPanelProps = {
  onSubmit: (payload: {
    tickers: string;
    account_size: number;
    risk_percent: number;
    max_dollar_risk: number | null;
    notes: string;
  }) => Promise<void>;
};

export function TickerInputPanel({ onSubmit }: TickerInputPanelProps) {
  const [tickers, setTickers] = useState("");
  const [accountSize, setAccountSize] = useState(100000);
  const [riskPercent, setRiskPercent] = useState(0.5);
  const [maxDollarRisk, setMaxDollarRisk] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const parsed = tickers.split(/[\s,]+/).filter(Boolean);
    if (parsed.length === 0) {
      setError("Enter at least one ticker.");
      return;
    }
    setError("");
    setSubmitting(true);
    try {
      await onSubmit({
        tickers,
        account_size: accountSize,
        risk_percent: riskPercent,
        max_dollar_risk: maxDollarRisk ? Number(maxDollarRisk) : null,
        notes
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start analysis.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="panel formGrid" onSubmit={handleSubmit}>
      <label>
        Tickers
        <textarea
          value={tickers}
          onChange={(event) => setTickers(event.target.value)}
          placeholder="NVDA, TSLA, COIN"
          rows={5}
        />
      </label>
      <label>
        Account size
        <input
          type="number"
          min="1"
          value={accountSize}
          onChange={(event) => setAccountSize(Number(event.target.value))}
        />
      </label>
      <label>
        Risk percent
        <select value={riskPercent} onChange={(event) => setRiskPercent(Number(event.target.value))}>
          <option value={0.25}>0.25%</option>
          <option value={0.5}>0.5%</option>
          <option value={1}>1.0%</option>
        </select>
      </label>
      <label>
        Max dollar risk
        <input
          type="number"
          min="1"
          value={maxDollarRisk}
          onChange={(event) => setMaxDollarRisk(event.target.value)}
          placeholder="Optional"
        />
      </label>
      <label>
        Notes
        <textarea value={notes} onChange={(event) => setNotes(event.target.value)} rows={3} />
      </label>
      {error && <div role="alert">{error}</div>}
      <button className="primaryButton" type="submit" disabled={submitting}>
        <Play size={18} />
        {submitting ? "Starting..." : "Start Analysis"}
      </button>
    </form>
  );
}
```

- [ ] **Step 4: Create Analyze page**

Create `frontend/src/pages/AnalyzePage.tsx`:

```tsx
import { createAnalysisRun } from "../api/client";
import { TickerInputPanel } from "../components/TickerInputPanel";

export function AnalyzePage() {
  return (
    <main className="page">
      <header className="pageHeader">
        <h1>Analyze</h1>
      </header>
      <TickerInputPanel
        onSubmit={async (payload) => {
          const run = await createAnalysisRun(payload);
          window.location.hash = `#/runs/${run.id}`;
        }}
      />
    </main>
  );
}
```

- [ ] **Step 5: Create job status table and run progress page**

Create `frontend/src/components/JobStatusTable.tsx`:

```tsx
import type { AnalysisJob } from "../types";

type JobStatusTableProps = {
  jobs: AnalysisJob[];
  onOpenTicker: (ticker: string) => void;
};

export function JobStatusTable({ jobs, onOpenTicker }: JobStatusTableProps) {
  return (
    <section className="panel">
      <table className="dataTable">
        <thead>
          <tr>
            <th>Ticker</th>
            <th>Status</th>
            <th>Error</th>
            <th>Report</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.id}>
              <td>{job.ticker}</td>
              <td>{job.status.replaceAll("_", " ")}</td>
              <td>{job.error_message ?? ""}</td>
              <td>
                {job.status === "complete" && (
                  <button type="button" onClick={() => onOpenTicker(job.ticker)}>
                    Open
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
```

Create `frontend/src/pages/RunProgressPage.tsx`:

```tsx
import { useEffect, useState } from "react";
import { fetchAnalysisRun, runMockAnalysis } from "../api/client";
import { JobStatusTable } from "../components/JobStatusTable";
import type { AnalysisRun } from "../types";

type RunProgressPageProps = {
  runId: number;
};

export function RunProgressPage({ runId }: RunProgressPageProps) {
  const [run, setRun] = useState<AnalysisRun | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchAnalysisRun(runId)
      .then(setRun)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load analysis run"));
  }, [runId]);

  async function runMock() {
    try {
      setRun(await runMockAnalysis(runId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run mock analysis");
    }
  }

  if (error) return <main className="page"><div className="panel" role="alert">{error}</div></main>;
  if (!run) return <main className="page"><div className="panel emptyState">Loading run...</div></main>;

  return (
    <main className="page">
      <header className="pageHeader">
        <h1>Analysis Run #{run.id}</h1>
        <button className="buttonLink" type="button" onClick={runMock}>
          Run Mock Analysis
        </button>
      </header>
      <JobStatusTable jobs={run.jobs} onOpenTicker={(ticker) => (window.location.hash = `#/ticker/${ticker}`)} />
    </main>
  );
}
```

- [ ] **Step 6: Update app routing and navigation**

Modify `frontend/src/App.tsx`:

```tsx
import { BarChart3, History, Search } from "lucide-react";
import { AnalyzePage } from "./pages/AnalyzePage";
import { RunProgressPage } from "./pages/RunProgressPage";
```

Update `Route`:

```ts
type Route =
  | { name: "dashboard" }
  | { name: "analyze" }
  | { name: "run"; runId: number }
  | { name: "history"; ticker?: string }
  | { name: "ticker"; ticker: string };
```

Update `routeFromHash`:

```ts
  if (hash === "analyze") return { name: "analyze" };
  if (hash.startsWith("runs/")) return { name: "run", runId: Number(hash.split("/")[1]) };
```

Replace Import nav:

```tsx
          <a className={route.name === "analyze" ? "active" : ""} href="#/analyze">
            <Search size={18} />
            Analyze
          </a>
```

Replace Import page render:

```tsx
        {route.name === "analyze" && <AnalyzePage />}
        {route.name === "run" && <RunProgressPage runId={route.runId} />}
```

- [ ] **Step 7: Write Analyze page tests**

Create `frontend/src/pages/AnalyzePage.test.tsx`:

```tsx
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { TickerInputPanel } from "../components/TickerInputPanel";

describe("TickerInputPanel", () => {
  it("requires at least one ticker", async () => {
    const onSubmit = vi.fn();
    render(<TickerInputPanel onSubmit={onSubmit} />);

    fireEvent.click(screen.getByRole("button", { name: /start analysis/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Enter at least one ticker.");
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits ticker and risk settings", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<TickerInputPanel onSubmit={onSubmit} />);

    fireEvent.change(screen.getByLabelText(/tickers/i), { target: { value: "NVDA, TSLA" } });
    fireEvent.click(screen.getByRole("button", { name: /start analysis/i }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalled());
    expect(onSubmit.mock.calls[0][0].tickers).toBe("NVDA, TSLA");
    expect(onSubmit.mock.calls[0][0].risk_percent).toBe(0.5);
  });
});
```

- [ ] **Step 8: Run frontend tests**

Run: `cd frontend && npm test -- --run src/pages/AnalyzePage.test.tsx`

Expected: PASS.

- [ ] **Step 9: Run full frontend tests**

Run: `cd frontend && npm test -- --run`

Expected: PASS after updating any snapshots or assertions that still expect the Import navigation.

- [ ] **Step 10: Commit**

```bash
git add frontend/src/types.ts frontend/src/api/client.ts frontend/src/App.tsx frontend/src/components/TickerInputPanel.tsx frontend/src/components/JobStatusTable.tsx frontend/src/pages/AnalyzePage.tsx frontend/src/pages/RunProgressPage.tsx frontend/src/pages/AnalyzePage.test.tsx
git commit -m "feat: add ticker analysis run UI"
```

---

### Task 5: Provider Adapter Interfaces and Mock Provider

**Files:**
- Create: `backend/paisapal/providers/__init__.py`
- Create: `backend/paisapal/providers/base.py`
- Create: `backend/paisapal/providers/mock.py`
- Create: `backend/tests/test_provider_adapters.py`

- [ ] **Step 1: Write failing provider tests**

Create `backend/tests/test_provider_adapters.py`:

```python
from paisapal.providers.mock import MockProvider


def test_mock_provider_returns_all_core_evidence_types():
    provider = MockProvider()

    evidence = provider.collect("NVDA")

    assert {item.source_type for item in evidence} == {
        "market",
        "fundamentals",
        "earnings",
        "options",
        "news_sentiment",
    }
    assert all(item.provider == "mock" for item in evidence)
    assert all(item.status == "fresh" for item in evidence)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m pytest backend/tests/test_provider_adapters.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'paisapal.providers'`.

- [ ] **Step 3: Add provider models and protocol**

Create `backend/paisapal/providers/__init__.py`:

```python
"""Market data provider adapters."""
```

Create `backend/paisapal/providers/base.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class EvidenceSnapshot:
    provider: str
    source_type: str
    status: str
    label: str
    payload: dict
    url: str | None = None
    warnings: list[str] = field(default_factory=list)
    retrieved_at: str = field(default_factory=utc_iso)

    def as_source_row(self) -> dict:
        return {
            "provider": self.provider,
            "source_type": self.source_type,
            "status": self.status,
            "label": self.label,
            "url": self.url,
            "payload": self.payload,
            "warnings": self.warnings,
        }


class MarketDataProvider(Protocol):
    name: str

    def collect(self, ticker: str) -> list[EvidenceSnapshot]:
        """Return normalized evidence snapshots for one ticker."""
```

- [ ] **Step 4: Add mock provider**

Create `backend/paisapal/providers/mock.py`:

```python
from __future__ import annotations

from paisapal.providers.base import EvidenceSnapshot


class MockProvider:
    name = "mock"

    def collect(self, ticker: str) -> list[EvidenceSnapshot]:
        return [
            EvidenceSnapshot(
                provider=self.name,
                source_type="market",
                status="fresh",
                label=f"Mock market snapshot for {ticker}",
                payload={"ticker": ticker, "current_price": 100.0, "volume": 1_000_000},
            ),
            EvidenceSnapshot(
                provider=self.name,
                source_type="fundamentals",
                status="fresh",
                label=f"Mock fundamentals for {ticker}",
                payload={"market_cap": 1_000_000_000, "pe_ratio": 30.0},
            ),
            EvidenceSnapshot(
                provider=self.name,
                source_type="earnings",
                status="fresh",
                label=f"Mock earnings for {ticker}",
                payload={"last_report": "mock", "eps_result": "beat"},
            ),
            EvidenceSnapshot(
                provider=self.name,
                source_type="options",
                status="fresh",
                label=f"Mock options for {ticker}",
                payload={"call_volume": 10000, "put_volume": 5000, "iv": 0.45},
            ),
            EvidenceSnapshot(
                provider=self.name,
                source_type="news_sentiment",
                status="fresh",
                label=f"Mock news sentiment for {ticker}",
                payload={"sentiment": "neutral-to-bullish"},
            ),
        ]
```

- [ ] **Step 5: Run provider tests**

Run: `python3 -m pytest backend/tests/test_provider_adapters.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/paisapal/providers backend/tests/test_provider_adapters.py
git commit -m "feat: add provider adapter interface"
```

---

### Task 6: Orchestrator Using Provider Evidence and Mock AI Output

**Files:**
- Create: `backend/paisapal/analysis_runs/orchestrator.py`
- Modify: `backend/paisapal/api/routes.py`
- Modify: `backend/tests/test_analysis_runs_api.py`

- [ ] **Step 1: Add failing orchestrator API assertion**

Append to `test_run_mock_analysis_completes_jobs_and_creates_reports` in `backend/tests/test_analysis_runs_api.py`:

```python
    report = client.get("/api/tickers/NVDA").json()
    assert "source_summary" in report["report"]
    assert report["report"]["source_summary"][0]["provider"] == "mock"
```

- [ ] **Step 2: Run the test to verify current source summary is insufficient if needed**

Run: `python3 -m pytest backend/tests/test_analysis_runs_api.py::test_run_mock_analysis_completes_jobs_and_creates_reports -v`

Expected: PASS if Task 3 already included source summary, or FAIL if the report response does not expose it. Continue either way to centralize orchestration.

- [ ] **Step 3: Add orchestrator**

Create `backend/paisapal/analysis_runs/orchestrator.py`:

```python
from __future__ import annotations

from sqlalchemy.orm import Session

from paisapal.analysis_runs.mock_pipeline import build_mock_report
from paisapal.db.repository import save_analysis_report, update_job_status
from paisapal.providers.base import MarketDataProvider
from paisapal.providers.mock import MockProvider


class AnalysisOrchestrator:
    def __init__(self, providers: list[MarketDataProvider] | None = None) -> None:
        self.providers = providers or [MockProvider()]

    def run_job(self, session: Session, job) -> None:
        try:
            update_job_status(session, job.id, "fetching_market_data")
            evidence = []
            for provider in self.providers:
                evidence.extend(provider.collect(job.ticker))

            update_job_status(session, job.id, "running_gpt_analysis")
            report = build_mock_report(job.ticker)
            report["source_summary"] = [
                {
                    "provider": item.provider,
                    "retrieved_at": item.retrieved_at,
                    "status": item.status,
                    "label": item.label,
                    "url": item.url,
                    "warnings": item.warnings,
                }
                for item in evidence
            ]
            save_analysis_report(
                session,
                job_id=job.id,
                report=report,
                source_snapshots=[item.as_source_row() for item in evidence],
            )
        except Exception as exc:
            update_job_status(session, job.id, "failed", str(exc))
```

- [ ] **Step 4: Use orchestrator from mock endpoint**

Modify `backend/paisapal/api/routes.py`:

```python
from paisapal.analysis_runs.orchestrator import AnalysisOrchestrator
```

Remove direct imports of `build_mock_report` and `build_mock_sources`.

Replace the loop body in `run_mock_analysis`:

```python
    orchestrator = AnalysisOrchestrator()
    for job in run.jobs:
        orchestrator.run_job(session, job)
```

- [ ] **Step 5: Run API tests**

Run: `python3 -m pytest backend/tests/test_analysis_runs_api.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/paisapal/analysis_runs/orchestrator.py backend/paisapal/api/routes.py backend/tests/test_analysis_runs_api.py
git commit -m "feat: orchestrate ticker analysis jobs"
```

---

### Task 7: OpenAI Structured Output Validation and Prompt Assembly

**Files:**
- Create: `backend/paisapal/ai/__init__.py`
- Create: `backend/paisapal/ai/schemas.py`
- Create: `backend/paisapal/ai/prompts.py`
- Create: `backend/tests/test_ai_output_validation.py`

- [ ] **Step 1: Write failing AI validation tests**

Create `backend/tests/test_ai_output_validation.py`:

```python
import pytest
from pydantic import ValidationError

from paisapal.ai.schemas import validate_ai_report


def valid_report():
    return {
        "ticker": "NVDA",
        "company_name": "NVIDIA Corporation",
        "current_price": 211.5,
        "final_classification": "Watchlist",
        "confidence": "Medium",
        "technical_rating": "Constructive",
        "vcp_rating": "Watchlist candidate",
        "fundamental_rating": "Very strong",
        "earnings_rating": "Strong",
        "sentiment_rating": "Bullish but crowded",
        "options_flow_rating": "Call-heavy",
        "risk_reward": 2.1,
        "entry_zones": ["$217-$219"],
        "stop_zones": ["$208-$209"],
        "target_zones": ["$228-$230"],
        "position_sizing": [],
        "bullish_factors": ["AI data center leadership"],
        "bearish_risks": ["Crowded expectations"],
        "data_warnings": [],
        "source_summary": [],
        "markdown_report": "# NVIDIA Corporation (NVDA) - Stock Analysis Report",
    }


def test_validate_ai_report_accepts_allowed_classification():
    report = validate_ai_report(valid_report())
    assert report.final_classification == "Watchlist"


def test_validate_ai_report_rejects_unapproved_classification():
    payload = valid_report()
    payload["final_classification"] = "Strong Buy"

    with pytest.raises(ValidationError):
        validate_ai_report(payload)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m pytest backend/tests/test_ai_output_validation.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'paisapal.ai'`.

- [ ] **Step 3: Add AI schemas**

Create `backend/paisapal/ai/__init__.py`:

```python
"""OpenAI-backed framework analysis."""
```

Create `backend/paisapal/ai/schemas.py`:

```python
from __future__ import annotations

from paisapal.analysis_runs.models import AiReportOutput


def validate_ai_report(payload: dict) -> AiReportOutput:
    return AiReportOutput.model_validate(payload)
```

- [ ] **Step 4: Add prompt assembly**

Create `backend/paisapal/ai/prompts.py`:

```python
from __future__ import annotations

import json

from paisapal.analysis_runs.models import AnalysisRunSettings
from paisapal.providers.base import EvidenceSnapshot


REPORT_SECTIONS = [
    "1. Current Stock Context",
    "2. VCP / Technical Pattern View",
    "3. Entry, Stop-Loss, and Target Zones",
    "4. SEPA-Style Position Sizing",
    "5. Earnings Review",
    "6. Fundamental Metrics",
    "7. Market Sentiment",
    "8. Options Flow / Implied Move",
    "9. Final View",
]


def build_framework_prompt(
    ticker: str,
    settings: AnalysisRunSettings,
    evidence: list[EvidenceSnapshot],
) -> str:
    evidence_payload = [
        {
            "provider": item.provider,
            "source_type": item.source_type,
            "status": item.status,
            "label": item.label,
            "payload": item.payload,
            "warnings": item.warnings,
            "retrieved_at": item.retrieved_at,
        }
        for item in evidence
    ]
    return "\n".join(
        [
            f"Run the PaisaPal investment framework for ticker {ticker}.",
            "Use the supplied evidence first. Use web research only for recent context and citations.",
            "Return structured JSON matching the AiReportOutput schema and include full Markdown.",
            "The Markdown report must use these sections:",
            json.dumps(REPORT_SECTIONS),
            "Final classification must be one of: Buy / Enter, Watchlist, Wait for Pullback, Avoid, Reduce, Exit.",
            f"User risk settings: {settings.model_dump_json()}",
            f"Evidence: {json.dumps(evidence_payload)}",
        ]
    )
```

- [ ] **Step 5: Run AI validation tests**

Run: `python3 -m pytest backend/tests/test_ai_output_validation.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/paisapal/ai backend/tests/test_ai_output_validation.py
git commit -m "feat: validate GPT investment report output"
```

---

### Task 8: OpenAI Client Behind Environment Configuration

**Files:**
- Modify: `pyproject.toml`
- Create: `backend/paisapal/ai/client.py`
- Modify: `backend/paisapal/analysis_runs/orchestrator.py`
- Create: `backend/tests/test_openai_client.py`

- [ ] **Step 1: Add dependencies**

Modify `pyproject.toml` dependencies:

```toml
dependencies = [
  "fastapi>=0.115.0",
  "httpx>=0.27.0",
  "openai>=1.99.0",
  "pydantic>=2.8.0",
  "python-multipart>=0.0.9",
  "sqlalchemy>=2.0.30",
  "uvicorn[standard]>=0.30.0"
]
```

- [ ] **Step 2: Sync dependencies**

Run: `/Users/shankars/Library/Python/3.9/bin/uv sync`

Expected: dependency lock updates successfully.

- [ ] **Step 3: Write OpenAI client tests**

Create `backend/tests/test_openai_client.py`:

```python
from paisapal.ai.client import OpenAiAnalysisClient


class FakeResponses:
    def create(self, **kwargs):
        self.kwargs = kwargs
        return type(
            "Response",
            (),
            {
                "output_text": """
{
  "ticker": "NVDA",
  "company_name": "NVIDIA Corporation",
  "current_price": 211.5,
  "final_classification": "Watchlist",
  "confidence": "Medium",
  "technical_rating": "Constructive",
  "vcp_rating": "Watchlist candidate",
  "fundamental_rating": "Very strong",
  "earnings_rating": "Strong",
  "sentiment_rating": "Bullish but crowded",
  "options_flow_rating": "Call-heavy",
  "risk_reward": 2.1,
  "entry_zones": [],
  "stop_zones": [],
  "target_zones": [],
  "position_sizing": [],
  "bullish_factors": [],
  "bearish_risks": [],
  "data_warnings": [],
  "source_summary": [],
  "markdown_report": "# NVIDIA Corporation (NVDA) - Stock Analysis Report"
}
""",
            },
        )()


class FakeOpenAI:
    def __init__(self):
        self.responses = FakeResponses()


def test_openai_analysis_client_validates_json_output():
    fake = FakeOpenAI()
    client = OpenAiAnalysisClient(openai_client=fake, model="gpt-5.5")

    report = client.analyze("prompt")

    assert report.ticker == "NVDA"
    assert fake.responses.kwargs["model"] == "gpt-5.5"
```

- [ ] **Step 4: Add OpenAI client**

Create `backend/paisapal/ai/client.py`:

```python
from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from paisapal.ai.schemas import validate_ai_report
from paisapal.analysis_runs.models import AiReportOutput


class OpenAiAnalysisClient:
    def __init__(self, openai_client: Any | None = None, model: str | None = None) -> None:
        self.client = openai_client or OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.5")

    def analyze(self, prompt: str) -> AiReportOutput:
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            tools=[{"type": "web_search_preview"}],
        )
        payload = json.loads(response.output_text)
        return validate_ai_report(payload)
```

- [ ] **Step 5: Run OpenAI client tests**

Run: `python3 -m pytest backend/tests/test_openai_client.py -v`

Expected: PASS.

- [ ] **Step 6: Keep orchestrator default on mock AI until live mode is explicit**

Modify `backend/paisapal/analysis_runs/orchestrator.py` constructor:

```python
class AnalysisOrchestrator:
    def __init__(
        self,
        providers: list[MarketDataProvider] | None = None,
        ai_client=None,
        use_live_ai: bool = False,
    ) -> None:
        self.providers = providers or [MockProvider()]
        self.ai_client = ai_client
        self.use_live_ai = use_live_ai
```

Replace report creation:

```python
            if self.use_live_ai and self.ai_client is not None:
                from paisapal.analysis_runs.models import AnalysisRunSettings
                from paisapal.ai.prompts import build_framework_prompt

                settings = AnalysisRunSettings(
                    account_size=job.run.account_size,
                    risk_percent=job.run.risk_percent,
                    max_dollar_risk=job.run.max_dollar_risk,
                    notes=job.run.notes,
                )
                prompt = build_framework_prompt(job.ticker, settings, evidence)
                report = self.ai_client.analyze(prompt).model_dump()
            else:
                report = build_mock_report(job.ticker)
```

- [ ] **Step 7: Run backend tests**

Run: `python3 -m pytest backend/tests -v`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml uv.lock backend/paisapal/ai/client.py backend/paisapal/analysis_runs/orchestrator.py backend/tests/test_openai_client.py
git commit -m "feat: add OpenAI report analysis client"
```

---

### Task 9: Real Provider Adapter Skeletons With Key-Aware Failover

**Files:**
- Create: `backend/paisapal/providers/alpha_vantage.py`
- Create: `backend/paisapal/providers/fmp.py`
- Create: `backend/paisapal/providers/polygon.py`
- Modify: `backend/paisapal/analysis_runs/orchestrator.py`
- Modify: `backend/tests/test_provider_adapters.py`

- [ ] **Step 1: Add tests for missing-key behavior**

Append to `backend/tests/test_provider_adapters.py`:

```python
from paisapal.providers.alpha_vantage import AlphaVantageProvider
from paisapal.providers.fmp import FmpProvider
from paisapal.providers.polygon import PolygonProvider


def test_unconfigured_real_providers_return_missing_snapshots():
    providers = [
        AlphaVantageProvider(api_key=None),
        FmpProvider(api_key=None),
        PolygonProvider(api_key=None),
    ]

    for provider in providers:
        evidence = provider.collect("NVDA")
        assert len(evidence) == 1
        assert evidence[0].status == "missing"
        assert "API key is not configured" in evidence[0].warnings
```

- [ ] **Step 2: Run provider tests to verify they fail**

Run: `python3 -m pytest backend/tests/test_provider_adapters.py -v`

Expected: FAIL with missing provider modules.

- [ ] **Step 3: Add Alpha Vantage skeleton**

Create `backend/paisapal/providers/alpha_vantage.py`:

```python
from __future__ import annotations

import os

from paisapal.providers.base import EvidenceSnapshot


class AlphaVantageProvider:
    name = "alpha_vantage"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("ALPHA_VANTAGE_API_KEY")

    def collect(self, ticker: str) -> list[EvidenceSnapshot]:
        if not self.api_key:
            return [
                EvidenceSnapshot(
                    provider=self.name,
                    source_type="provider_status",
                    status="missing",
                    label="Alpha Vantage",
                    payload={"ticker": ticker},
                    warnings=["API key is not configured"],
                )
            ]
        return [
            EvidenceSnapshot(
                provider=self.name,
                source_type="provider_status",
                status="fresh",
                label="Alpha Vantage configured",
                payload={"ticker": ticker},
            )
        ]
```

- [ ] **Step 4: Add FMP skeleton**

Create `backend/paisapal/providers/fmp.py`:

```python
from __future__ import annotations

import os

from paisapal.providers.base import EvidenceSnapshot


class FmpProvider:
    name = "fmp"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("FMP_API_KEY")

    def collect(self, ticker: str) -> list[EvidenceSnapshot]:
        if not self.api_key:
            return [
                EvidenceSnapshot(
                    provider=self.name,
                    source_type="provider_status",
                    status="missing",
                    label="Financial Modeling Prep",
                    payload={"ticker": ticker},
                    warnings=["API key is not configured"],
                )
            ]
        return [
            EvidenceSnapshot(
                provider=self.name,
                source_type="provider_status",
                status="fresh",
                label="Financial Modeling Prep configured",
                payload={"ticker": ticker},
            )
        ]
```

- [ ] **Step 5: Add Polygon skeleton**

Create `backend/paisapal/providers/polygon.py`:

```python
from __future__ import annotations

import os

from paisapal.providers.base import EvidenceSnapshot


class PolygonProvider:
    name = "polygon"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("POLYGON_API_KEY")

    def collect(self, ticker: str) -> list[EvidenceSnapshot]:
        if not self.api_key:
            return [
                EvidenceSnapshot(
                    provider=self.name,
                    source_type="provider_status",
                    status="missing",
                    label="Polygon",
                    payload={"ticker": ticker},
                    warnings=["API key is not configured"],
                )
            ]
        return [
            EvidenceSnapshot(
                provider=self.name,
                source_type="provider_status",
                status="fresh",
                label="Polygon configured",
                payload={"ticker": ticker},
            )
        ]
```

- [ ] **Step 6: Run provider tests**

Run: `python3 -m pytest backend/tests/test_provider_adapters.py -v`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/paisapal/providers/alpha_vantage.py backend/paisapal/providers/fmp.py backend/paisapal/providers/polygon.py backend/tests/test_provider_adapters.py
git commit -m "feat: add key-aware market data providers"
```

---

### Task 10: Dashboard and Ticker Report Redesign for AI Reports

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/components/WatchlistTable.tsx`
- Create: `frontend/src/components/SourceSummary.tsx`
- Modify: `frontend/src/pages/DashboardPage.tsx`
- Modify: `frontend/src/pages/TickerDetailPage.tsx`
- Modify: `frontend/src/pages/DashboardPage.test.tsx`
- Modify: `frontend/src/pages/TickerDetailPage.test.tsx`

- [ ] **Step 1: Expand report types**

Modify `TickerReport` in `frontend/src/types.ts`:

```ts
export type SourceSummaryItem = {
  provider: string;
  retrieved_at: string;
  status: string;
  label: string;
  url: string | null;
  warnings: string[];
};

export type TickerReport = {
  ticker: string;
  report: {
    ticker?: string;
    company_name?: string;
    current_price?: number;
    final_classification?: string;
    confidence?: string;
    technical_rating?: string;
    vcp_rating?: string;
    fundamental_rating?: string;
    earnings_rating?: string;
    sentiment_rating?: string;
    options_flow_rating?: string;
    data_warnings?: string[];
    source_summary?: SourceSummaryItem[];
    input?: Record<string, unknown>;
    analysis?: Record<string, unknown>;
  };
  markdown_report: string;
  created_at: string;
};
```

- [ ] **Step 2: Create source summary component**

Create `frontend/src/components/SourceSummary.tsx`:

```tsx
import type { SourceSummaryItem } from "../types";

type SourceSummaryProps = {
  sources: SourceSummaryItem[];
};

export function SourceSummary({ sources }: SourceSummaryProps) {
  if (sources.length === 0) {
    return <p>No source summary was stored for this report.</p>;
  }

  return (
    <table className="dataTable">
      <thead>
        <tr>
          <th>Provider</th>
          <th>Status</th>
          <th>Label</th>
          <th>Warnings</th>
        </tr>
      </thead>
      <tbody>
        {sources.map((source, index) => (
          <tr key={`${source.provider}-${index}`}>
            <td>{source.provider}</td>
            <td>{source.status}</td>
            <td>{source.url ? <a href={source.url}>{source.label}</a> : source.label}</td>
            <td>{source.warnings.join(", ")}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

- [ ] **Step 3: Update ticker detail page to render AI Markdown**

Replace report body in `frontend/src/pages/TickerDetailPage.tsx` after header:

```tsx
      <ReportSection title="Source & Freshness">
        <SourceSummary sources={report.report.source_summary ?? []} />
      </ReportSection>
      {(report.report.data_warnings ?? []).length > 0 && (
        <ReportSection title="Data Warnings">
          <ul>
            {(report.report.data_warnings ?? []).map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </ReportSection>
      )}
      <ReportSection title="Generated Report">
        <pre className="markdownReport">{report.markdown_report}</pre>
      </ReportSection>
```

Add import:

```tsx
import { SourceSummary } from "../components/SourceSummary";
```

- [ ] **Step 4: Update watchlist table columns**

Modify `frontend/src/components/WatchlistTable.tsx` to include these headers and fields:

```tsx
<th>Ticker</th>
<th>Price</th>
<th>Classification</th>
<th>Confidence</th>
<th>Technical</th>
<th>Fundamentals</th>
<th>Earnings</th>
<th>Sentiment</th>
<th>Options</th>
<th>Risk/Reward</th>
<th>Updated</th>
```

Use `row.final_decision` as the classification field until the backend response is renamed in a later cleanup.

- [ ] **Step 5: Run frontend tests**

Run: `cd frontend && npm test -- --run`

Expected: PASS after updating assertions to match `Analyze` navigation and AI report labels.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/types.ts frontend/src/components/WatchlistTable.tsx frontend/src/components/SourceSummary.tsx frontend/src/pages/DashboardPage.tsx frontend/src/pages/TickerDetailPage.tsx frontend/src/pages/DashboardPage.test.tsx frontend/src/pages/TickerDetailPage.test.tsx
git commit -m "feat: display AI analysis reports"
```

---

### Task 11: Documentation and Local Configuration

**Files:**
- Modify: `README.md`
- Create: `.env.example`

- [ ] **Step 1: Add environment example**

Create `.env.example`:

```bash
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.5
POLYGON_API_KEY=
ALPHA_VANTAGE_API_KEY=
FMP_API_KEY=
```

- [ ] **Step 2: Update README workflow**

Replace the CSV-first sections in `README.md` with:

```markdown
## Analysis Workflow

PaisaPal accepts a set of tickers, creates one analysis job per ticker, gathers market evidence from configured providers, supplements it with GPT web-search research, and generates a framework report using GPT-5.5.

The report follows:

1. Current Stock Context
2. VCP / Technical Pattern View
3. Entry, Stop-Loss, and Target Zones
4. SEPA-Style Position Sizing
5. Earnings Review
6. Fundamental Metrics
7. Market Sentiment
8. Options Flow / Implied Move
9. Final View

## Environment

Copy `.env.example` to `.env` and fill the keys you want to use:

```bash
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.5
POLYGON_API_KEY=
ALPHA_VANTAGE_API_KEY=
FMP_API_KEY=
```

Provider keys are optional for local UI development. Missing providers are recorded as missing evidence and should lower confidence in generated analysis.
```

- [ ] **Step 3: Run docs sanity check**

Run: `rg -n "CSV Import|sample_watchlist|csv driven|csv-driven" README.md frontend/src backend/paisapal`

Expected: only legacy CSV module names or explicitly deferred cleanup references remain. The main README and navigation should no longer describe CSV as the primary workflow.

- [ ] **Step 4: Commit**

```bash
git add README.md .env.example
git commit -m "docs: document AI ticker analysis setup"
```

---

### Task 12: End-to-End Verification and Cleanup

**Files:**
- No planned file changes. If verification exposes a defect, edit the exact failing file and include it in the verification-fix commit.

- [ ] **Step 1: Run backend tests**

Run: `python3 -m pytest backend/tests -v`

Expected: PASS.

- [ ] **Step 2: Run frontend tests**

Run: `cd frontend && npm test -- --run`

Expected: PASS.

- [ ] **Step 3: Run backend server**

Run: `./scripts/dev_backend.sh`

Expected: FastAPI starts on `http://127.0.0.1:8000`.

- [ ] **Step 4: Run frontend server in a second shell**

Run: `cd frontend && npm run dev`

Expected: Vite starts on `http://127.0.0.1:5173`.

- [ ] **Step 5: Manual smoke test**

In the browser:

1. Open `http://127.0.0.1:5173`.
2. Navigate to Analyze.
3. Enter `NVDA, TSLA`.
4. Start analysis.
5. Open the created run page.
6. Run mock analysis.
7. Open the NVDA report.
8. Confirm the report shows Source & Freshness and Generated Report.
9. Return to Dashboard and confirm NVDA and TSLA appear.

Expected: the full keyless mocked flow works without CSV import.

- [ ] **Step 6: Commit verification fixes**

If verification required fixes:

```bash
git add <fixed-files>
git commit -m "fix: stabilize ticker analysis workflow"
```

If no fixes were needed, do not create an empty commit.

---

## Future Follow-Up Plan

After this plan lands, write a second implementation plan for live provider endpoint details. That plan should add real HTTP calls one provider at a time with fixtures for exact payloads, because provider response shapes and paid-plan availability vary by account.
