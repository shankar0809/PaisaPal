# Provider Fallback Adapters Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Tiingo, Finnhub, SimFin, and FRED adapters so live runs can fill earnings, sentiment, fundamentals, macro, market, and technical evidence when current providers are rate-limited or plan-limited.

**Architecture:** Follow the existing `MarketDataProvider.collect(ticker)` adapter contract with injectable HTTP clients, key-aware missing snapshots, redacted provider errors, and compact normalized payloads. Wire configured keys into the provider factory and provider-status endpoint without changing the analysis-run API.

**Tech Stack:** Python 3.12, httpx, pytest, FastAPI, existing `EvidenceSnapshot` model.

---

### Task 1: Provider Tests

**Files:**
- Modify: `backend/tests/test_provider_adapters.py`

- [ ] Add fake HTTP clients and failing tests for Tiingo, Finnhub, SimFin, and FRED normalized snapshots.
- [ ] Add missing-key tests for the four new providers.
- [ ] Run targeted tests and verify they fail because the providers are not implemented.

### Task 2: Provider Implementations

**Files:**
- Create: `backend/paisapal/providers/tiingo.py`
- Create: `backend/paisapal/providers/finnhub.py`
- Create: `backend/paisapal/providers/simfin.py`
- Create: `backend/paisapal/providers/fred.py`

- [ ] Implement Tiingo market, technical, and news sentiment evidence.
- [ ] Implement Finnhub market, earnings, and news sentiment evidence.
- [ ] Implement SimFin fundamentals, financials, and ratios evidence.
- [ ] Implement FRED macro evidence.
- [ ] Run provider adapter tests and Ruff.

### Task 3: Wiring and Status

**Files:**
- Modify: `backend/paisapal/analysis_runs/orchestrator.py`
- Modify: `backend/paisapal/api/routes.py`
- Modify: `backend/paisapal/analysis_runs/source_coverage.py`
- Modify: `backend/tests/test_analysis_runs_api.py`

- [ ] Add configured providers when matching env keys are present.
- [ ] Add `/api/provider-status` rows for Tiingo, Finnhub, SimFin, and FRED.
- [ ] Teach source coverage that macro evidence supports current context and final view.
- [ ] Run API tests.

### Task 4: Docs and Verification

**Files:**
- Modify: `README.md`

- [ ] Document new provider coverage.
- [ ] Run backend tests and Ruff.
