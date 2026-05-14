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

The app is informational only and is not financial advice.
