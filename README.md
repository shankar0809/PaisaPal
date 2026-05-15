# PaisaPal

PaisaPal is a local single-user investment analysis app. It accepts a set of tickers, creates one analysis job per ticker, gathers market evidence from configured providers, supplements it with GPT web-search research, and generates a framework report using GPT-5.5.

The app is informational only and is not financial advice.

## Local Development

Backend:

```bash
uv sync
./scripts/dev_backend.sh
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://127.0.0.1:5173`. The backend runs at `http://127.0.0.1:8000`.

## Analysis Workflow

Enter one or more tickers from the Analyze screen. PaisaPal creates one job for each ticker, collects structured evidence from available providers, records source freshness, and generates a report that follows:

1. Current Stock Context
2. VCP / Technical Pattern View
3. Entry, Stop-Loss, and Target Zones
4. SEPA-Style Position Sizing
5. Earnings Review
6. Fundamental Metrics
7. Market Sentiment
8. Options Flow / Implied Move
9. Final View

Provider keys are optional for local UI development. When `ALPHA_VANTAGE_API_KEY` is set, the live run collects Alpha Vantage daily price, company overview, earnings, and news sentiment evidence. When `FMP_API_KEY` is set, the live run collects Financial Modeling Prep company profile, financial statements, ratios, health scores, and earnings evidence. When no market-data keys are configured, the app falls back to mock evidence so the UI remains usable.

Use the regular **Run Analysis** action for configured live providers and GPT commentary. The backend still exposes `/api/analysis-runs/{run_id}/run-mock` for deterministic local testing.

## Environment

Copy `.env.example` to `.env` and fill the keys you want to use:

```bash
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.5
POLYGON_API_KEY=
ALPHA_VANTAGE_API_KEY=
FMP_API_KEY=
```

## Local Data

The backend stores local data in `paisapal.sqlite`. This database is ignored by Git.

## Current Capabilities

- Ticker-based analysis runs
- Per-ticker job progress
- Provider availability status
- Alpha Vantage evidence for market data, fundamentals, earnings, and news sentiment
- Financial Modeling Prep evidence for fundamentals, financial statements, ratios, health scores, and earnings
- Mock evidence fallback for keyless local development
- GPT-5.5 report validation and prompt assembly
- Watchlist dashboard
- Ticker report view with source freshness
- Snapshot history
- Markdown report export
