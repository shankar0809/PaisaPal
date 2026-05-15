# Polygon Provider Design

## Goal

Add Polygon as the third live market-data provider so PaisaPal can enrich each ticker analysis with price-action context, technical bars, and options-chain evidence.

## Scope

This slice replaces the Polygon provider skeleton with a tested HTTP adapter. It does not add new UI screens, run background async jobs, or build a full options-flow analytics engine. It supplies compact evidence for GPT analysis using the same provider boundary as Alpha Vantage and FMP.

## Data Sources

Use Polygon REST endpoints:

- `/v3/reference/tickers/{ticker}` for ticker reference details such as name, market, exchange, type, CIK, SIC, and market cap when available.
- `/v3/snapshot` with `ticker={ticker}`, `type=stocks`, and `limit=1` for current/near-current stock snapshot data including session metrics, last trade/quote fields where available, and market status.
- `/v2/aggs/ticker/{ticker}/range/1/day/{from}/{to}` for recent daily OHLCV bars used to summarize price action and compute simple moving averages.
- `/v3/snapshot/options/{ticker}` for option-chain snapshot evidence such as implied volatility, open interest, greeks, break-even price, contract details, and underlying price where available.

All requests include `apiKey={POLYGON_API_KEY}`.

## Architecture

`PolygonProvider` will follow the existing provider pattern:

- constructor accepts `api_key`, injectable `http_client`, `timeout`, `end_date`, and `lookback_days`
- missing API key returns one `provider_status` snapshot with `status="missing"`
- live requests return normalized `EvidenceSnapshot` instances
- HTTP exceptions or provider error payloads return one `provider_status` error snapshot and stop collection
- `configured_providers()` already includes `PolygonProvider` when `POLYGON_API_KEY` is set

## Evidence Output

Return these source types:

- `market`: ticker reference plus stock snapshot/session information.
- `technicals`: recent daily bars and derived price-action summary such as latest close, 20-day moving average, 50-day moving average, high/low over the fetched range, and average volume.
- `options`: compact option-chain snapshot rows for the first returned contracts, including contract type, strike, expiration, implied volatility, open interest, greeks, day change, break-even price, and underlying price.

Payloads should be compact and AI-friendly. Numeric strings should be converted to numbers where practical.

## Error Handling

If Polygon returns a payload with `status` such as `ERROR`, `NOT_AUTHORIZED`, or an error/message field indicating a provider failure, return one error snapshot with the endpoint name and warning text. Empty result lists are allowed and produce fresh evidence with empty rows.

## Tests

Add tests in `backend/tests/test_provider_adapters.py` using a fake HTTP client:

- configured Polygon returns `market`, `technicals`, and `options`
- request paths match ticker overview, unified snapshot, daily aggregates, and options chain
- requests include `apiKey`
- aggregate request includes `adjusted=True`, `sort="asc"`, and a limit
- normalized technical payload includes latest close, moving averages, range high/low, and average volume
- option payload includes implied volatility, open interest, delta, strike, expiration, and underlying price
- provider error responses return one `provider_status` error snapshot
- missing-key behavior remains unchanged

## Documentation

Update `README.md` to list Polygon as a live evidence provider when `POLYGON_API_KEY` is set.

## Acceptance Criteria

- Backend provider tests pass.
- Full backend test suite passes.
- Ruff passes.
- Frontend tests/build still pass because the UI run flow is unchanged.
- Changes are committed, merged into `main`, and pushed to `origin/main` after verification.
