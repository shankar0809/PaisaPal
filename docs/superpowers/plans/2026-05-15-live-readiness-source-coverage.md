# Live Readiness and Source Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show whether live analysis is ready before running and show framework section source coverage on generated reports.

**Architecture:** Extend existing API response models in a backward-compatible way, add a small source coverage derivation helper, and render the new metadata in existing Analyze and ticker report pages.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, pytest, React, TypeScript, Vite, Vitest, Testing Library.

---

## Files

- Modify: `backend/paisapal/api/schemas.py`
- Modify: `backend/paisapal/api/routes.py`
- Create: `backend/paisapal/analysis_runs/source_coverage.py`
- Modify: `backend/tests/test_analysis_runs_api.py`
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/pages/AnalyzePage.tsx`
- Create: `frontend/src/components/ProviderReadiness.tsx`
- Create: `frontend/src/components/FrameworkSourceCoverage.tsx`
- Modify: `frontend/src/pages/TickerDetailPage.tsx`
- Modify: `frontend/src/pages/AnalyzePage.test.tsx`
- Modify: `frontend/src/pages/TickerDetailPage.test.tsx`

## Task 1: Backend Readiness and Coverage

- [ ] Add failing backend tests for `/api/provider-status` readiness metadata and ticker report `source_coverage`.
- [ ] Extend `ProviderStatusResponse` with `role`, `required_for_live`, `live_ready`, and `message`.
- [ ] Extend `TickerReportResponse` with `source_coverage`.
- [ ] Implement `derive_source_coverage(report: dict) -> list[dict]`.
- [ ] Update routes to return readiness and coverage.
- [ ] Run `uv run pytest backend/tests/test_analysis_runs_api.py -v`.
- [ ] Run `uv run ruff check backend`.
- [ ] Commit `feat: expose live readiness and source coverage`.

## Task 2: Frontend Readiness and Coverage UI

- [ ] Add failing frontend tests for Analyze readiness panel and ticker detail source coverage.
- [ ] Extend frontend types for provider readiness and source coverage.
- [ ] Add `ProviderReadiness` component and wire it into `AnalyzePage`.
- [ ] Add `FrameworkSourceCoverage` component and wire it into `TickerDetailPage`.
- [ ] Run `npm test -- --run src/pages/AnalyzePage.test.tsx src/pages/TickerDetailPage.test.tsx`.
- [ ] Run full frontend tests/build.
- [ ] Commit `feat: show live readiness and source coverage`.

## Task 3: Final Verification and Merge

- [ ] Run `/Users/shankars/Library/Python/3.9/bin/uv run pytest backend/tests -q`
- [ ] Run `/Users/shankars/Library/Python/3.9/bin/uv run ruff check backend`
- [ ] Run `cd frontend && npm test -- --run && npm run build`
- [ ] Merge to `main`, rerun verification on `main`, push to `origin/main`.

## Self-Review

- Spec coverage: readiness, coverage derivation, Analyze UI, report UI, and verification are covered.
- Placeholder scan: no unresolved placeholders.
- Type consistency: response/type names align with existing API and frontend client patterns.
