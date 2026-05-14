# Local Investment Analysis App Design

## Goal

Build a local single-user browser app for importing CSV watchlists, running the investment analysis framework from the PDF spec, comparing ticker opportunities, and drilling into a full framework report for each stock.

The first version is intentionally local-only. It does not require authentication, hosting, brokerage integration, live market data APIs, or AI commentary.

## Product Shape

The app opens to a watchlist dashboard. The user imports a CSV where each row represents one ticker and contains the stock context, technical inputs, trade plan, fundamentals scores, sentiment fields, and options-flow fields needed by the framework.

After import, the backend validates each row, normalizes the values, saves the batch to SQLite, runs the deterministic analysis rules, and stores an analysis snapshot. The dashboard then shows each ticker with its final decision, confidence, technical rating, fundamentals rating, sentiment rating, options-flow rating, risk/reward, and last analyzed time.

Clicking a ticker opens a drill-down report. The report follows the investment framework sections:

- Current stock context
- VCP / technical pattern
- Entry, target, and stop-loss
- SEPA-style position sizing
- Last 8 earnings summary
- Fundamental metrics
- Market sentiment
- Options flow / implied move
- LEAP analysis
- Upcoming earnings implied move
- Final directional recommendation

Every report should show both the imported inputs and calculated outputs so that decisions are traceable.

## Architecture

Use a local full-stack web app:

- Backend: Python FastAPI
- Database: SQLite
- Frontend: React + Vite
- Analysis engine: pure Python package with no database or web dependency

The analysis engine is the core domain layer. It calculates VCP score, fundamentals rating, sentiment/crowding risk, options-flow rating, earnings quality, risk/reward, position size, LEAP suitability, earnings implied move, and final decision.

FastAPI owns CSV import, validation, persistence, analysis snapshot creation, and JSON API endpoints. React owns the user experience: CSV upload, preview, dashboard, filters, drill-down report, history view, and export actions.

Data flow:

```text
CSV upload
  -> FastAPI validates and normalizes rows
  -> SQLite stores import batch and ticker rows
  -> analysis engine calculates ratings and final decisions
  -> SQLite stores analysis snapshots
  -> React dashboard and report views display results
```

This separation keeps the framework rules testable and makes it straightforward to add live market data or hosted deployment later.

## Core Screens

### Dashboard

The dashboard is the home screen. It shows a watchlist table with:

- Ticker
- Current price
- Final decision
- Confidence
- Technical rating
- Fundamentals rating
- Sentiment rating
- Options-flow rating
- Risk/reward
- Last analyzed time

The dashboard includes filters for final decision, technical rating, fundamentals rating, and sentiment. It supports sorting by risk/reward, confidence, ticker, and updated time.

### CSV Import

The CSV import screen supports:

- File upload
- Parsed-row preview
- Row and column validation errors
- Unknown-column warnings
- Import-batch creation
- Immediate analysis after successful import

Rows with validation errors are not saved. Valid rows can still be imported if other rows fail.

### Ticker Detail

The ticker detail page shows the full framework report for one ticker. Each section displays relevant inputs and calculated outputs.

The final recommendation section must always end with exactly one decision:

- Buy / Enter
- Watchlist
- Wait for Pullback
- Avoid
- Reduce
- Exit

### Analysis History

The history view lists prior analysis snapshots for a ticker. It shows decision changes over time, including the previous final decision, current final decision, and timestamp.

## CSV Input

The v1 CSV is one row per ticker.

Required columns:

```text
ticker,current_price,week_52_high,week_52_low,resistance,support,ma_20,ma_50,ma_200,relative_strength,sector_trend,market_trend,entry,stop_loss,target_1,target_2
```

Optional columns:

```text
market_cap,upcoming_catalyst,
vcp_strong_prior_uptrend,vcp_above_rising_50_day,vcp_above_rising_200_day,vcp_relative_strength_improving,vcp_orderly_consolidation,vcp_smaller_pullbacks,vcp_volume_drying_up,vcp_tightening_near_resistance,vcp_clear_pivot,vcp_strong_breakout_volume,
fund_revenue_growth,fund_eps_growth,fund_gross_margin,fund_operating_margin,fund_free_cash_flow,fund_balance_sheet,fund_valuation,fund_segment_strength,fund_guidance,fund_capital_return,
analyst_sentiment,news_sentiment,short_interest_signal,insider_activity_signal,sector_sentiment,stock_rallied_sharply,call_heavy_options,valuation_elevated,earnings_near,
call_volume,put_volume,call_open_interest,put_open_interest,iv_rank,iv_percentile,expected_move
```

Validation rules:

- `ticker` must be non-empty and is normalized to uppercase.
- Price, support/resistance, target, stop, and moving-average fields must be positive numbers.
- `stop_loss` must be below `entry`.
- `target_1` and `target_2` must be above `entry`.
- Fundamental score fields must be integers from 1 to 5.
- Boolean fields accept `true/false`, `yes/no`, and `1/0`.
- Unknown columns are ignored during import and shown as warnings in the preview.

Earnings history and LEAP chains are modeled in the app but are not part of the first CSV format. They will be added as separate import types after the core watchlist flow works.

## Build Phases

### Phase 1: Local App Foundation

Set up FastAPI, React/Vite, SQLite, test tooling, and local run scripts. The app should start locally with one backend command and one frontend command.

### Phase 2: Analysis Engine

Implement the deterministic rules from the PDF as pure Python:

- Current context classification
- VCP scoring
- Risk/reward calculation
- SEPA-style position sizing
- Fundamentals scoring
- Sentiment and crowding classification
- Options-flow classification
- Final recommendation engine

### Phase 3: CSV Import

Implement CSV upload, preview, validation, import-batch storage, valid-row import, and analysis snapshot creation.

### Phase 4: Dashboard

Build the watchlist table with filters, sorting, final-decision badges, and ticker drill-down navigation.

### Phase 5: Ticker Detail Report

Build the framework report view with all major sections and traceable inputs/calculated outputs.

### Phase 6: Analysis History

Persist snapshots over time and show previous analyses for each ticker.

### Phase 7: Polish

Add Markdown export, sample CSV download, helpful empty states, error states, and README instructions.

## Testing Strategy

Backend tests:

- Analysis rules unit tests
- CSV parsing tests
- Validation tests
- API tests for import, dashboard rows, ticker detail, and history

Frontend tests:

- CSV import preview rendering
- Dashboard table rendering
- Filter and sort behavior
- Ticker detail section rendering

End-to-end smoke test:

- Upload sample CSV
- Confirm rows appear in dashboard
- Open ticker detail
- Confirm final decision appears in the report

## Deferred Work

The following items are intentionally outside v1:

- User accounts
- Cloud deployment
- Brokerage connections
- Live market data providers
- AI-generated commentary
- Alerts and notifications
- Portfolio tracking
- Multi-user collaboration

## Success Criteria

The v1 app is successful when:

- A user can run the app locally.
- A user can upload a valid CSV watchlist.
- The app validates CSV rows and reports errors clearly.
- Valid rows are saved to SQLite.
- Each valid ticker receives a deterministic analysis snapshot.
- The dashboard supports filtering and sorting.
- A ticker detail page shows the full framework-style report.
- Prior snapshots are visible in analysis history.
- The generated report always ends with one final decision.
