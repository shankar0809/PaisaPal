# Free Market Data Providers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add free market-data providers and make them the default provider stack for local screening.

**Architecture:** Add focused provider classes for Yahoo chart data, SEC CompanyFacts fundamentals, and Stooq daily CSV fallback. Update provider selection to honor `MARKET_DATA_MODE=free` and only append paid providers when `ENABLE_PAID_PROVIDER_FALLBACK=true`.

**Tech Stack:** Python, httpx, FastAPI, pytest, existing `EvidenceSnapshot` provider protocol.

---

### Task 1: Free Provider Tests

**Files:**
- Modify: `backend/tests/test_provider_adapters.py`
- Modify: `backend/tests/test_analysis_runs_api.py`

- [ ] Add failing tests for Yahoo, SEC, and Stooq provider normalization.
- [ ] Add failing tests for free-mode provider selection and paid fallback opt-in.
- [ ] Run targeted tests and verify they fail because the providers do not exist yet.

### Task 2: Free Provider Implementations

**Files:**
- Create: `backend/paisapal/providers/yahoo.py`
- Create: `backend/paisapal/providers/sec_edgar.py`
- Create: `backend/paisapal/providers/stooq.py`
- Modify: `backend/paisapal/analysis_runs/orchestrator.py`

- [ ] Implement Yahoo chart provider.
- [ ] Implement SEC CompanyFacts provider.
- [ ] Implement Stooq CSV provider.
- [ ] Update provider selection for free mode and paid fallback.
- [ ] Run targeted provider tests.

### Task 3: API Status and Configuration

**Files:**
- Modify: `backend/paisapal/api/routes.py`
- Modify: `.env`
- Modify: `README.md`

- [ ] Add free provider readiness rows to `/api/provider-status`.
- [ ] Configure `.env` for `MARKET_DATA_MODE=free`.
- [ ] Document free mode and paid fallback.
- [ ] Run API tests.

### Task 4: End-to-End Verification

**Files:**
- No code changes expected.

- [ ] Run `uv run pytest`.
- [ ] Run `uv run ruff check backend`.
- [ ] Run `npm test`.
- [ ] Run `npm run build`.
- [ ] Run an NVDA analysis with free providers plus local Ollama.
