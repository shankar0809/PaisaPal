# Live Readiness and Source Coverage Design

## Goal

Make it obvious when the app is ready to run live AI analysis and which framework sections are supported by provider evidence in a generated report.

## Scope

This slice adds backend-derived readiness/coverage metadata and displays it in the existing Analyze and ticker report screens. It does not change provider adapters, the report-generation schema, or add new navigation.

## Backend Design

Extend `/api/provider-status` to return:

- per-provider rows for `openai`, `alpha_vantage`, `fmp`, and `polygon`
- `role`: `ai`, `market_data`, or `fundamentals`
- `required_for_live`: true for OpenAI and false for individual market data providers
- `live_ready`: true when `OPENAI_API_KEY` exists and at least one market-data provider key exists
- `message`: a short status message such as `Live AI analysis ready` or `Configure OPENAI_API_KEY and at least one market data provider`

Keep the response backward compatible by preserving existing `provider` and `configured` fields.

For ticker reports, derive `source_coverage` from the stored `report.source_summary` provider/source metadata. The initial implementation can use source summary labels and provider names because source snapshots are saved separately and not currently returned by `/api/tickers/{ticker}`. Coverage sections:

- Current Stock Context
- VCP / Technical Pattern View
- Entry, Stop-Loss, and Target Zones
- SEPA-Style Position Sizing
- Earnings Review
- Fundamental Metrics
- Market Sentiment
- Options Flow / Implied Move
- Final View

Each coverage row includes:

- `section`
- `status`: `covered`, `partial`, or `missing`
- `matched_sources`
- `warnings`

## Frontend Design

Analyze screen:

- Fetch `/api/provider-status` on load.
- Show a compact readiness panel above the ticker form.
- Surface whether live analysis is ready or fallback/mock-only.
- Show configured/missing provider chips for OpenAI, Alpha Vantage, FMP, and Polygon.

Ticker detail screen:

- Add a `Framework Source Coverage` section above the existing source table.
- Show coverage rows with section, status, and matched source labels.
- Keep existing source freshness and generated Markdown sections unchanged.

## Testing

Backend:

- provider status returns live readiness metadata when OpenAI plus a provider key are present
- provider status reports not ready when OpenAI or all market-data keys are missing
- ticker report response includes derived source coverage

Frontend:

- Analyze page renders readiness and configured/missing providers
- Ticker detail page renders framework source coverage

## Acceptance Criteria

- Backend tests pass.
- Ruff passes.
- Frontend tests/build pass.
- Changes are committed, merged to `main`, and pushed to `origin/main`.
