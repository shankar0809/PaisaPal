# Local Ollama AI Provider Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add local Ollama report generation as a selectable replacement for OpenAI while preserving live market-data providers.

**Architecture:** Introduce an AI client factory that selects OpenAI or Ollama from environment configuration. The orchestrator keeps using the same prompt and report schema, so reports, watchlist rows, and source summaries remain compatible.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, httpx, OpenAI Python SDK, Ollama HTTP API, pytest.

---

### Task 1: Add Ollama AI Client

**Files:**
- Modify: `backend/paisapal/ai/client.py`
- Test: `backend/tests/test_openai_client.py`

- [ ] Add tests for a successful Ollama JSON response and invalid JSON retry behavior.
- [ ] Implement `OllamaAnalysisClient` using `httpx.Client`.
- [ ] Reuse `validate_ai_report` and the existing correction retry pattern.
- [ ] Run `uv run pytest backend/tests/test_openai_client.py -v`.

### Task 2: Add AI Client Selection

**Files:**
- Modify: `backend/paisapal/ai/client.py`
- Modify: `backend/paisapal/api/routes.py`
- Test: `backend/tests/test_analysis_runs_api.py`

- [ ] Add `build_analysis_client()` and `selected_ai_provider_status()` helpers.
- [ ] Use `AI_PROVIDER=openai|ollama` to choose the AI client.
- [ ] Update `/api/provider-status` to report `openai` or `ollama` as the active AI provider.
- [ ] Update `run_analysis` to use the selected AI client.
- [ ] Run `uv run pytest backend/tests/test_analysis_runs_api.py -v`.

### Task 3: Configure Local Mode

**Files:**
- Modify: `.env`
- Modify: `README.md`

- [ ] Set local AI mode in `.env` with `AI_PROVIDER=ollama`, `OLLAMA_BASE_URL`, and `OLLAMA_MODEL`.
- [ ] Document local Ollama mode and fallback OpenAI mode in `README.md`.
- [ ] Keep existing market-data API key configuration unchanged.

### Task 4: Verify End to End

**Files:**
- No code changes expected.

- [ ] Run `uv run pytest`.
- [ ] Run `npm test`.
- [ ] Run `npm run build`.
- [ ] Install Ollama if missing.
- [ ] Pull the configured local model.
- [ ] Start or verify the Ollama server.
- [ ] Run an NVDA analysis through the backend and confirm it uses live market data plus local AI.
