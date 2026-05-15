# AI Live Investment Analysis App Design

## Goal

Rework PaisaPal from a CSV-driven dashboard into a local investment research app that accepts a set of ticker symbols, gathers current market information from multiple sources, runs the existing framework PDF through GPT-5.5, and produces detailed per-ticker investment analysis reports for decision support.

The existing framework PDF remains the authoritative analysis framework:

- `docs/specs/Generic_Stock_Trading_Investment_Analysis_Framework_Spec.pdf`

The reference reports supplied for HOOD, INTC, MU, TSLA, COIN, and NVDA define the target report shape, tone, and level of detail. Reports should remain research and planning tools, not financial advice.

## Product Shape

The primary workflow starts with ticker entry, not CSV import. The user enters a comma-separated or line-separated set of tickers, configures risk assumptions, and starts an analysis run. The app creates one analysis job per ticker, gathers structured market data, supplements it with GPT web-search research, runs the framework step by step, and stores the resulting dashboard summary and full report.

The generated report should follow this structure:

1. Current Stock Context
2. VCP / Technical Pattern View
3. Entry, Stop-Loss, and Target Zones
4. SEPA-Style Position Sizing
5. Earnings Review
6. Fundamental Metrics
7. Market Sentiment
8. Options Flow / Implied Move
9. Final View

Each report must include a data source and freshness note so the user can see which fields came from structured provider APIs, which came from GPT web search, and where data was missing or stale.

## Architecture

Use the existing local full-stack app shape:

- Backend: Python FastAPI
- Database: SQLite
- Frontend: React + Vite
- AI: OpenAI Responses API using GPT-5.5
- Data access: provider adapter layer plus GPT web-search research

The backend owns analysis orchestration. The frontend owns ticker entry, job progress, dashboard comparison, report display, history, and export actions.

Data flow:

```text
Ticker list
  -> FastAPI validates and normalizes symbols
  -> SQLite stores an analysis run and per-ticker jobs
  -> provider adapters fetch structured data
  -> GPT web search gathers recent qualitative context and citations
  -> GPT-5.5 runs the framework against collected evidence
  -> backend validates structured AI output
  -> SQLite stores source snapshots, dashboard summary, and full report
  -> React displays progress, comparison dashboard, detail reports, and history
```

This keeps numeric inputs traceable while still allowing GPT web search to capture recent catalysts, analyst tone, regulatory context, sentiment shifts, and other qualitative factors that structured APIs may miss.

## Data Source Strategy

Use a provider adapter layer. The app should not depend on a single market-data vendor.

Initial adapters:

- Market and technical data: Polygon and Alpha Vantage.
- Fundamentals, ratios, financial statements, and earnings: Financial Modeling Prep and Alpha Vantage.
- Options volume, open interest, implied volatility, and implied move: Polygon and Alpha Vantage where available.
- News and sentiment: Alpha Vantage news sentiment and GPT web-search research.

Provider calls should normalize into internal evidence objects:

- `MarketSnapshot`
- `TechnicalSnapshot`
- `FundamentalSnapshot`
- `EarningsSnapshot`
- `OptionsSnapshot`
- `NewsSentimentSnapshot`
- `WebResearchSnapshot`

Every evidence object should record:

- Provider name
- Retrieval timestamp
- Source URL or endpoint label
- Raw payload reference or compact raw JSON
- Normalized fields
- Missing-field notes
- Confidence/freshness status

When providers disagree, the app should preserve source-level values and let the GPT analysis explain material conflicts instead of silently averaging them.

## GPT Analysis Contract

GPT-5.5 receives:

- The framework PDF text or extracted framework instructions.
- The collected structured evidence.
- GPT web-search findings with citations.
- The user risk settings.
- The reference report style instructions derived from the supplied reports.

GPT-5.5 must return validated structured output plus a report body.

Structured output fields:

- Ticker
- Company name
- Current price reference
- Final classification
- Confidence score
- Technical rating
- VCP rating
- Fundamental rating
- Earnings rating
- Sentiment rating
- Options-flow rating
- Risk/reward summary
- Suggested entry zones
- Stop zones
- Target zones
- Position-sizing scenarios
- Key bullish factors
- Key bearish risks
- Missing or stale data warnings
- Source summary
- Full report Markdown

The final classification must be exactly one of:

- Buy / Enter
- Watchlist
- Wait for Pullback
- Avoid
- Reduce
- Exit

The report can include nuanced language, but the structured final classification must be one of those values so dashboard filtering stays reliable.

## Core Screens

### Analyze

The Analyze screen replaces CSV Import as the primary entry point. It supports:

- Ticker input as comma-separated or line-separated symbols.
- Account size and maximum dollar risk settings.
- Risk percentage presets such as 0.25%, 0.5%, and 1.0%.
- Optional analysis notes from the user.
- Start-analysis action.

The screen should validate symbols locally before submitting and show obvious duplicate or malformed tickers.

### Job Progress

The job progress view shows one row per ticker with stages:

- Queued
- Fetching market data
- Fetching fundamentals
- Fetching earnings
- Fetching options data
- Running web research
- Running GPT framework analysis
- Complete
- Failed

Failures should be per ticker. One failed ticker should not block the rest of the run.

### Dashboard

The dashboard compares latest analyses across tickers. It shows:

- Ticker
- Current price reference
- Final classification
- Confidence
- Technical rating
- Fundamental rating
- Earnings rating
- Sentiment rating
- Options-flow rating
- Risk/reward summary
- Data freshness
- Last analyzed time

It supports filtering by final classification, rating, stale-data status, and run date. Sorting should support confidence, ticker, updated time, and risk/reward.

### Ticker Report

The ticker detail page shows the full generated report. It follows the nine-section report structure from the reference reports and includes:

- Source/freshness notes
- Missing-data warnings
- Structured recommendation fields
- Full Markdown report
- Export actions for Markdown and PDF

### History

The history view lists prior analysis snapshots for a ticker. It shows final classification changes, confidence changes, price references, and report timestamps.

## API Surface

- `GET /api/health` - backend health check.
- `POST /api/analysis-runs` - create an analysis run from tickers and settings.
- `GET /api/analysis-runs/{run_id}` - get run status and per-ticker job status.
- `GET /api/analysis-runs/{run_id}/events` - stream job progress if server-sent events are used.
- `GET /api/watchlist` - latest dashboard rows.
- `GET /api/tickers/{ticker}` - latest full analysis report.
- `GET /api/tickers/{ticker}/history` - prior reports for one ticker.
- `GET /api/tickers/{ticker}/report.md` - latest report as Markdown.
- `GET /api/tickers/{ticker}/report.pdf` - latest report as PDF.
- `GET /api/provider-status` - configured provider keys and availability without exposing secrets.

Existing CSV endpoints can be removed from the main navigation. A future CSV feature may return as bulk ticker input only, not as the source of analysis values.

## Data Model

SQLite tables:

- `analysis_runs`: one user-triggered run with tickers, settings, and timestamps.
- `analysis_jobs`: one row per ticker per run, including status, errors, and timing.
- `source_snapshots`: normalized and raw provider evidence per ticker/job/source.
- `analysis_reports`: structured GPT output, full Markdown report, final classification, ratings, and source summary.

The app should store enough raw source context to audit a report later without re-fetching every provider.

## Error Handling

Provider failures should degrade gracefully:

- Missing options data should produce an options-data warning and a lower confidence score, not fail the whole report.
- Missing fundamentals should mark fundamentals incomplete and ask GPT to treat conclusions conservatively.
- API rate limits should mark affected jobs retryable.
- GPT output validation failures should retry once with the validation errors, then fail the ticker with a clear message.
- GPT web-search failures should still allow provider-only analysis, but the report must state that recent web context was unavailable.

## Configuration

Configuration should come from environment variables:

- `OPENAI_API_KEY`
- `OPENAI_MODEL`, defaulting to `gpt-5.5`
- `POLYGON_API_KEY`
- `ALPHA_VANTAGE_API_KEY`
- `FMP_API_KEY`
- Provider timeout and retry settings

The app should show whether each provider is configured, but it must never expose API keys in frontend responses or logs.

## Testing Strategy

Backend tests:

- Ticker normalization and validation.
- Provider adapter normalization with mocked API responses.
- Provider fallback behavior.
- GPT prompt assembly with fixture evidence.
- GPT structured-output validation.
- Analysis run and job persistence.
- Per-ticker failure isolation.
- Report export.

Frontend tests:

- Analyze screen validation and submission.
- Job progress rendering.
- Dashboard filtering and sorting.
- Ticker report rendering.
- Missing-data and failed-job states.

Integration tests:

- Mock providers and mock GPT response.
- Submit multiple tickers.
- Confirm jobs complete independently.
- Confirm dashboard rows and full reports are stored.

Live API tests should be opt-in only because they require keys, network access, cost, and rate-limit handling.

## Build Phases

### Phase 1: Replace CSV Entry With Ticker Runs

Add analysis-run and job models, ticker-entry UI, run creation endpoint, and job progress states. Use mocked analysis output initially.

### Phase 2: Provider Adapter Layer

Implement market, fundamentals, earnings, options, and news adapter interfaces with mocked tests. Add real adapters incrementally behind environment-key checks.

### Phase 3: GPT Framework Analysis

Extract or encode the framework instructions, assemble prompts from evidence, call GPT-5.5 with structured output, validate the response, and store reports.

### Phase 4: Dashboard and Report Redesign

Update dashboard fields, ticker detail report, source/freshness display, and history view for AI-generated analysis.

### Phase 5: GPT Web-Search Research Layer

Add cited web-search research as an evidence source for recent catalysts, analyst tone, market sentiment, regulatory context, and news. Make web-search failures non-blocking.

### Phase 6: Export and Polish

Add Markdown/PDF export, provider-status screen, retry controls, useful empty states, and README setup instructions.

## Deferred Work

- Brokerage integration
- Trade execution
- Alerts and notifications
- Cloud deployment
- User accounts
- Portfolio tracking
- Paid-data entitlement management beyond local API-key configuration
- Automatic scheduled analysis runs

## Success Criteria

The redesign is successful when:

- The user can enter a set of tickers without preparing a CSV.
- The app creates independent analysis jobs for each ticker.
- The app gathers structured market data from configured providers.
- The app supplements provider data with GPT web-search research.
- GPT-5.5 produces a report matching the supplied reference report structure.
- Each ticker receives a structured final classification and dashboard summary.
- Reports include source and freshness notes.
- Partial data does not silently produce overconfident analysis.
- Prior reports are retained for history and comparison.
