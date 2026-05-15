# FMP Provider Design

## Goal

Add Financial Modeling Prep as the second live market-data provider so PaisaPal can enrich each ticker analysis with deeper fundamentals, financial statements, ratios, health scores, and earnings evidence.

## Scope

This slice adds a real `FmpProvider` implementation behind the existing provider adapter boundary. It does not change the report schema, add new UI screens, or implement Polygon/options data.

## Data Sources

Use Financial Modeling Prep stable endpoints:

- `profile?symbol={ticker}` for company profile, sector, industry, beta, price, market cap, and description.
- `income-statement?symbol={ticker}&limit=4` for recent revenue, gross profit, operating income, net income, EPS, and margin context.
- `balance-sheet-statement?symbol={ticker}&limit=4` for cash, debt, assets, liabilities, and equity context.
- `cash-flow-statement?symbol={ticker}&limit=4` for operating cash flow, capex, and free cash flow context.
- `ratios?symbol={ticker}&limit=4` for profitability, liquidity, valuation, and leverage ratios.
- `key-metrics?symbol={ticker}&limit=4` for valuation and per-share metrics.
- `financial-scores?symbol={ticker}` for Piotroski/Altman-style health signals where available.
- `earnings?symbol={ticker}&limit=8` for earnings dates, EPS estimates, actual EPS, and revenue estimates where available.

All requests include `apikey={FMP_API_KEY}`.

## Architecture

`FmpProvider` will follow the existing `AlphaVantageProvider` pattern:

- constructor accepts `api_key`, injectable `http_client`, and `timeout`
- missing API key returns one `provider_status` snapshot with `status="missing"`
- live requests return normalized `EvidenceSnapshot` instances
- provider errors, rate limits, or unexpected HTTP/JSON errors return one `provider_status` snapshot with `status="error"` and a warning
- `configured_providers()` already includes `FmpProvider` when `FMP_API_KEY` is set, so no route change is required unless tests expose a wiring gap

## Evidence Output

The provider should return these source types:

- `fundamentals`: profile snapshot with company identity, sector, industry, price, beta, market cap, and description.
- `financials`: compact recent income statement, balance sheet, and cash flow rows.
- `ratios`: recent ratios, key metrics, and financial scores.
- `earnings`: recent earnings rows.

Payloads should be compact and AI-friendly, with numeric strings converted to numbers where practical and only the most recent rows retained.

## Error Handling

If any endpoint returns an object containing an FMP error-like field such as `Error Message`, `error`, `message`, or `Information`, the provider returns one error snapshot for that endpoint and does not continue. HTTP exceptions are handled the same way. Empty list responses are allowed and produce fresh snapshots with empty lists.

## Tests

Add tests in `backend/tests/test_provider_adapters.py` using a fake HTTP client:

- configured FMP returns `fundamentals`, `financials`, `ratios`, and `earnings`
- requests use stable endpoint paths and include `symbol`, `limit` where needed, and `apikey`
- numeric fields are normalized into `int`/`float`
- provider error responses return one `provider_status` error snapshot
- missing-key behavior remains unchanged

## Documentation

Update `README.md` to list FMP as a live evidence provider when `FMP_API_KEY` is set.

## Acceptance Criteria

- Backend provider tests pass.
- Full backend test suite passes.
- Ruff passes.
- Frontend tests/build still pass because the UI run flow is unchanged.
- Changes are committed, merged into `main`, and pushed to `origin/main` after verification.
