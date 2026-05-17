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

Provider keys are optional for local UI development. When `ALPHA_VANTAGE_API_KEY` is set, the live run collects Alpha Vantage daily price, company overview, earnings, and news sentiment evidence. When `FMP_API_KEY` is set, the live run collects Financial Modeling Prep company profile, financial statements, ratios, health scores, and earnings evidence. When `POLYGON_API_KEY` is set, the live run collects Polygon stock snapshots, daily bars, technical summaries, and options-chain evidence. `TIINGO_API_KEY`, `FINNHUB_API_KEY`, `SIMFIN_API_KEY`, and `FRED_API_KEY` add fallback market/news, earnings/options/news, financial statement, and macro evidence. When no market-data keys are configured, the app falls back to mock evidence so the UI remains usable.

Use the regular **Run Analysis** action for configured live providers and AI commentary. The backend still exposes `/api/analysis-runs/{run_id}/run-mock` for deterministic local testing.

## AI Provider

PaisaPal can generate reports with OpenAI or a local Ollama model.

Local Ollama mode keeps API costs down by using your local machine for report generation while still using configured market-data APIs:

```bash
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:7b-instruct
```

Install Ollama, start it, and pull the configured model:

```bash
ollama pull qwen2.5:7b-instruct
```

OpenAI mode remains available:

```bash
AI_PROVIDER=openai
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.4-mini
```

Local models are slower and may be less reliable at strict JSON output than OpenAI. If a local model fails validation, the backend retries once and records the validation error on the job if it still cannot produce a valid report.

## Market Data Provider

PaisaPal defaults to free market-data mode for local screening:

```bash
MARKET_DATA_MODE=free
ENABLE_PAID_PROVIDER_FALLBACK=false
SEC_USER_AGENT="PaisaPal local app your-email@example.com"
```

Free mode uses:

- Yahoo Finance chart data for quotes and daily bars.
- SEC EDGAR CompanyFacts for U.S. company fundamentals and financial statement facts.
- Stooq daily CSV data as a keyless price-history fallback using the direct CSV endpoint.

Paid providers remain available as fallback when you explicitly opt in:

```bash
ENABLE_PAID_PROVIDER_FALLBACK=true
```

Set `MARKET_DATA_MODE=paid` to use only configured paid providers. Free mode does not provide reliable options flow, realtime quotes, or rich news sentiment; those report sections are marked missing or lower-confidence when no source-backed evidence exists.

Configured paid and fallback providers are best-effort. If one endpoint is rate-limited or plan-gated, PaisaPal keeps successful snapshots from that provider and appends a redacted provider-status warning for the failed endpoint.

## Environment

Copy `.env.example` to `.env` and fill the keys you want to use:

```bash
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:7b-instruct
MARKET_DATA_MODE=free
ENABLE_PAID_PROVIDER_FALLBACK=false
SEC_USER_AGENT="PaisaPal local app your-email@example.com"
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.4-mini
TIINGO_API_KEY=
FINNHUB_API_KEY=
SIMFIN_API_KEY=
FRED_API_KEY=
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
- Free market-data mode with Yahoo Finance, SEC EDGAR, and Stooq
- Alpha Vantage evidence for market data, fundamentals, earnings, and news sentiment
- Financial Modeling Prep evidence for fundamentals, financial statements, ratios, health scores, and earnings
- Polygon evidence for stock snapshots, technical daily bars, and options chains
- Tiingo evidence for market data, daily bars, and company news
- Finnhub evidence for quotes, earnings, company news, and options chains
- SimFin evidence for fundamentals, financial statements, and derived ratios
- FRED evidence for macroeconomic context
- Mock evidence fallback for keyless local development
- OpenAI and local Ollama report validation and prompt assembly
- Watchlist dashboard
- Ticker report view with source freshness
- Snapshot history
- Markdown report export
