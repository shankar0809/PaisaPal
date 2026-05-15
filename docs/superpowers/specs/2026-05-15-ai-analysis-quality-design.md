# AI Analysis Quality Design

## Goal

Improve report quality and reliability now that live provider evidence exists from Alpha Vantage, FMP, and Polygon.

## Scope

This slice is backend-focused. It upgrades prompt construction, evidence organization, and OpenAI output validation/retry behavior. It does not add new UI screens, change the persisted report schema, or run real provider/API calls in tests.

## Design

Add an evidence mapping layer that groups raw provider snapshots into the investment-framework sections:

- Current Stock Context: `market`, `fundamentals`
- VCP / Technical Pattern View: `market`, `technicals`
- Entry, Stop-Loss, and Target Zones: `market`, `technicals`
- SEPA-Style Position Sizing: `market`, `technicals`
- Earnings Review: `earnings`
- Fundamental Metrics: `fundamentals`, `financials`, `ratios`
- Market Sentiment: `news_sentiment`
- Options Flow / Implied Move: `options`
- Final View: all available evidence and provider-status warnings

`build_framework_prompt()` will include both the raw evidence snapshots and this framework evidence map. The prompt will explicitly require section-by-section, source-backed analysis, callouts for missing/weak evidence, and no invented confidence when provider data is missing.

`OpenAiAnalysisClient` will request structured output using the Responses API `text.format` JSON schema configuration and continue validating with the local `AiReportOutput` Pydantic model. If parsing or validation fails, it will retry once with the validation error appended to the prompt so the model can repair the JSON. After retries are exhausted, the validation error bubbles to the orchestrator, which already marks the job failed.

## Error Handling

- Invalid JSON raises a retry.
- Schema validation failures raise a retry.
- The final failed validation is not swallowed; job failure is preferable to saving an unreliable report.
- Provider warnings remain in `source_summary`; prompt instructions require the model to reflect them in `data_warnings`.

## Tests

Add backend tests for:

- evidence mapping assigns provider snapshots to the correct framework sections
- prompt includes the framework evidence map and explicit missing-evidence instructions
- OpenAI client sends a JSON schema response format
- OpenAI client retries after invalid output and returns the repaired validated report

## Acceptance Criteria

- Backend tests pass.
- Ruff passes.
- Frontend tests/build still pass.
- Changes are committed, merged into `main`, and pushed to `origin/main`.
