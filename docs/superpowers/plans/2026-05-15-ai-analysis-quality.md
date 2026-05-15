# AI Analysis Quality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve GPT report quality by mapping evidence to framework sections and enforcing structured JSON output with retry.

**Architecture:** Add a small evidence mapping module used by prompt construction. Upgrade the OpenAI client to send a JSON schema response format and retry once when JSON parsing or Pydantic validation fails.

**Tech Stack:** Python 3.12, Pydantic, pytest, Ruff, OpenAI Responses API.

---

## Files

- Create: `backend/paisapal/ai/evidence_map.py`
- Modify: `backend/paisapal/ai/prompts.py`
- Modify: `backend/paisapal/ai/client.py`
- Modify: `backend/tests/test_ai_output_validation.py`
- Modify: `backend/tests/test_openai_client.py`

## Task 1: Evidence Mapping and Prompt Upgrade

- [ ] Add failing tests in `backend/tests/test_ai_output_validation.py` for `build_framework_evidence_map()` and prompt content.
- [ ] Implement `backend/paisapal/ai/evidence_map.py` with section-to-source-type mapping.
- [ ] Update `build_framework_prompt()` to include `framework_evidence_map` JSON and instructions for missing evidence and source-backed commentary.
- [ ] Run `uv run pytest backend/tests/test_ai_output_validation.py -v`.
- [ ] Commit with `feat: map evidence to framework sections`.

## Task 2: Structured Output and Retry

- [ ] Add failing tests in `backend/tests/test_openai_client.py` asserting JSON schema response format and retry after invalid output.
- [ ] Update `OpenAiAnalysisClient` to pass `text={"format": {"type": "json_schema", ...}}`.
- [ ] Add retry behavior for JSON parse and validation failures.
- [ ] Run `uv run pytest backend/tests/test_openai_client.py -v`.
- [ ] Commit with `feat: enforce structured AI report output`.

## Task 3: Verification

- [ ] Run backend tests: `/Users/shankars/Library/Python/3.9/bin/uv run pytest backend/tests -q`
- [ ] Run Ruff: `/Users/shankars/Library/Python/3.9/bin/uv run ruff check backend`
- [ ] Run frontend tests/build: `cd frontend && npm test -- --run && npm run build`
- [ ] Merge to `main`, rerun verification on `main`, and push.

## Self-Review

- Spec coverage: evidence mapping, prompt upgrade, structured output, retry, and verification are covered.
- Placeholder scan: no unresolved placeholders.
- Type consistency: all code uses existing `EvidenceSnapshot`, `AnalysisRunSettings`, and `AiReportOutput` contracts.
