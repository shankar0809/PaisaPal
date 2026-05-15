# PaisaPal

PaisaPal is a local single-user investment analysis app. It imports CSV watchlists, runs a deterministic framework for technicals, fundamentals, sentiment, options flow, risk, and final decision, then displays a dashboard and ticker reports.

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

## CSV Import

Use `examples/sample_watchlist.csv` as the starting format.

Required columns:

```text
ticker,current_price,week_52_high,week_52_low,resistance,support,ma_20,ma_50,ma_200,relative_strength,sector_trend,market_trend,entry,stop_loss,target_1,target_2
```

Optional columns include VCP flags, fundamental scores, sentiment fields, and options-flow values. The app validates stop-loss, targets, positive price fields, ticker values, and score ranges before saving rows.

## Local Data

The backend stores local data in `paisapal.sqlite`. This database is ignored by Git.

## Current Capabilities

- CSV preview and validation
- SQLite-backed import batches and analysis snapshots
- Deterministic analysis rules
- Watchlist dashboard
- Ticker report view
- Snapshot history
- Markdown report export

The app is informational only and is not financial advice.
