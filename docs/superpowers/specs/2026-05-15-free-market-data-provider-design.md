# Free Market Data Provider Design

## Goal

PaisaPal should support a free market-data mode for normal screening runs. The mode should avoid paid Polygon, FMP, and Alpha Vantage dependencies by default while preserving the existing paid providers as optional fallback.

## User Experience

The user can configure:

```bash
MARKET_DATA_MODE=free
ENABLE_PAID_PROVIDER_FALLBACK=false
SEC_USER_AGENT=PaisaPal local app your-email@example.com
```

With this configuration, Run Analysis uses free providers first and local Ollama can generate the report without OpenAI API cost.

## Provider Stack

- Yahoo Finance chart endpoint: daily OHLCV history and current quote context.
- SEC EDGAR CompanyFacts: U.S. public-company fundamentals and financial-statement facts.
- Stooq daily CSV endpoint: fallback historical daily OHLCV data.
- Paid providers: Alpha Vantage, FMP, and Polygon only when explicitly enabled.

## Data Flow

1. The orchestrator asks `configured_providers()` for market-data providers.
2. In free mode, it returns Yahoo, SEC, and Stooq.
3. If `ENABLE_PAID_PROVIDER_FALLBACK=true`, configured paid providers are appended after free providers.
4. Each provider returns `EvidenceSnapshot` rows using the existing source types.
5. The AI prompt and report persistence paths remain unchanged.

## Error Handling

Each free provider returns a provider-status error snapshot rather than raising through the run. Unofficial endpoints are treated as best-effort. SEC requests include a configurable User-Agent so the app follows SEC automated access expectations.

## Testing

Tests should cover:

- Yahoo chart response normalization.
- Stooq CSV response normalization.
- SEC ticker-to-CIK lookup and CompanyFacts normalization.
- Free-mode provider selection.
- Paid fallback opt-in.
- Provider status output for free mode.
