# Alpha Vantage Provider Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Alpha Vantage provider skeleton with tested real HTTP evidence collection for market, fundamentals, earnings, and news sentiment data.

**Architecture:** Keep the provider adapter boundary from the AI live analysis work. `AlphaVantageProvider` will accept an injectable HTTP client for tests, normalize each endpoint response into `EvidenceSnapshot`, preserve missing/rate-limit/error responses as evidence, and remain key-aware so local development still works without provider credentials.

**Tech Stack:** Python 3.12, `httpx`, pytest, FastAPI/SQLAlchemy existing backend, Alpha Vantage JSON APIs.

---

## Source Documents

- Product spec: `docs/superpowers/specs/2026-05-15-ai-live-investment-analysis-app-design.md`
- Alpha Vantage official docs: `https://www.alphavantage.co/documentation/`
- Endpoints used first:
  - `TIME_SERIES_DAILY`
  - `OVERVIEW`
  - `EARNINGS`
  - `NEWS_SENTIMENT`

## File Structure

- Modify: `backend/paisapal/providers/alpha_vantage.py` - real key-aware HTTP collection and normalization.
- Modify: `backend/tests/test_provider_adapters.py` - fixture-driven provider tests.
- Modify: `backend/paisapal/analysis_runs/orchestrator.py` - provider factory for configured live providers while keeping mock default.
- Modify: `backend/tests/test_analysis_runs_api.py` - provider selection/status test if orchestration wiring changes.
- Modify: `README.md` - document that Alpha Vantage is the first live provider.

## Task 1: Alpha Vantage HTTP Provider

**Files:**
- Modify: `backend/paisapal/providers/alpha_vantage.py`
- Modify: `backend/tests/test_provider_adapters.py`

- [ ] **Step 1: Write failing provider normalization tests**

Add tests that inject a fake HTTP client returning payloads for:

- `TIME_SERIES_DAILY`
- `OVERVIEW`
- `EARNINGS`
- `NEWS_SENTIMENT`

Assert `AlphaVantageProvider(api_key="key", http_client=fake).collect("NVDA")` returns source types:

```python
{"market", "fundamentals", "earnings", "news_sentiment"}
```

Assert endpoint params include the Alpha Vantage `function`, `symbol` or `tickers`, and `apikey`.

- [ ] **Step 2: Verify tests fail**

Run:

```bash
/Users/shankars/Library/Python/3.9/bin/uv run pytest backend/tests/test_provider_adapters.py -v
```

Expected: FAIL because `AlphaVantageProvider` does not accept `http_client` and only returns provider-status evidence.

- [ ] **Step 3: Implement minimal HTTP collection**

Use `httpx.Client` when no client is injected. Request each endpoint from `https://www.alphavantage.co/query` with a timeout. Return one `EvidenceSnapshot` per successful endpoint.

- [ ] **Step 4: Handle provider warnings as evidence**

If Alpha Vantage returns `Note`, `Information`, or `Error Message`, return a snapshot with `status="error"`, `source_type="provider_status"`, and the message in `warnings`.

- [ ] **Step 5: Verify tests pass**

Run:

```bash
/Users/shankars/Library/Python/3.9/bin/uv run pytest backend/tests/test_provider_adapters.py -v
/Users/shankars/Library/Python/3.9/bin/uv run pytest backend/tests -q
/Users/shankars/Library/Python/3.9/bin/uv run ruff check backend
```

- [ ] **Step 6: Commit**

```bash
git add backend/paisapal/providers/alpha_vantage.py backend/tests/test_provider_adapters.py
git commit -m "feat: fetch Alpha Vantage evidence"
```

## Task 2: Configured Provider Selection

**Files:**
- Modify: `backend/paisapal/analysis_runs/orchestrator.py`
- Modify: `backend/paisapal/api/routes.py`
- Modify: `backend/tests/test_analysis_runs_api.py`

- [ ] **Step 1: Write failing provider selection test**

Add a test that sets `ALPHA_VANTAGE_API_KEY` and verifies a provider factory returns `AlphaVantageProvider` instead of only `MockProvider`.

- [ ] **Step 2: Implement provider factory**

Add `configured_providers()` that returns configured real providers, falling back to `[MockProvider()]` when none are configured.

- [ ] **Step 3: Wire mock run to keep mock behavior**

Keep `/run-mock` using explicit `AnalysisOrchestrator(providers=[MockProvider()])` so keyless and deterministic UI smoke tests remain stable.

- [ ] **Step 4: Add future live endpoint only if needed**

Do not expose a live-cost endpoint unless the route can remain opt-in and tested without network.

- [ ] **Step 5: Verify and commit**

Run backend tests and ruff, then commit:

```bash
git add backend/paisapal/analysis_runs/orchestrator.py backend/paisapal/api/routes.py backend/tests/test_analysis_runs_api.py
git commit -m "feat: select configured market data providers"
```

## Task 3: Documentation and Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Document Alpha Vantage**

Add that Alpha Vantage currently supplies market, fundamentals, earnings, and news sentiment evidence when `ALPHA_VANTAGE_API_KEY` is set.

- [ ] **Step 2: Run full verification**

Run:

```bash
/Users/shankars/Library/Python/3.9/bin/uv run pytest backend/tests -q
/Users/shankars/Library/Python/3.9/bin/uv run ruff check backend
cd frontend && npm test -- --run && npm run build
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: document Alpha Vantage evidence provider"
```

