# Polygon Provider Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a tested Polygon provider that supplies stock snapshot, technical daily bar, and options-chain evidence for live ticker analysis.

**Architecture:** Follow the existing provider adapter pattern: injectable HTTP client, key-aware missing snapshots, provider error snapshots, and compact normalized `EvidenceSnapshot` payloads. The existing `configured_providers()` factory already instantiates `PolygonProvider`, so this slice replaces the skeleton without route changes.

**Tech Stack:** Python 3.12, `httpx`, pytest, Ruff, Polygon REST APIs, FastAPI provider adapter boundary.

---

## Files

- Modify: `backend/paisapal/providers/polygon.py` - implement real Polygon HTTP collection and normalization.
- Modify: `backend/tests/test_provider_adapters.py` - add Polygon provider behavior tests with fake HTTP client.
- Modify: `README.md` - document Polygon evidence coverage.

## Task 1: Polygon HTTP Provider

**Files:**
- Modify: `backend/tests/test_provider_adapters.py`
- Modify: `backend/paisapal/providers/polygon.py`

- [ ] **Step 1: Write the failing success test**

Add fake Polygon response/client classes and a test that calls:

```python
provider = PolygonProvider(
    api_key="demo-key",
    http_client=http_client,
    end_date=date(2026, 5, 15),
)
evidence = provider.collect("NVDA")
```

Expected source types:

```python
{"market", "technicals", "options"}
```

Expected normalized fields:

```python
market.payload["ticker"] == "NVDA"
market.payload["name"] == "NVIDIA Corporation"
technicals.payload["latest_close"] == 130.0
technicals.payload["sma_20"] == 120.5
technicals.payload["range_high"] == 132.0
technicals.payload["average_volume"] == 1500000
options.payload["contracts"][0]["implied_volatility"] == 0.55
options.payload["contracts"][0]["delta"] == 0.62
```

Expected request paths:

```python
[
    "/v3/reference/tickers/NVDA",
    "/v3/snapshot",
    "/v2/aggs/ticker/NVDA/range/1/day/2026-01-15/2026-05-15",
    "/v3/snapshot/options/NVDA",
]
```

All requests must include `apiKey="demo-key"`. The aggregate request must include `adjusted=True`, `sort="asc"`, and `limit=120`.

- [ ] **Step 2: Run the success test to verify it fails**

Run:

```bash
/Users/shankars/Library/Python/3.9/bin/uv run pytest backend/tests/test_provider_adapters.py::test_polygon_provider_collects_live_evidence_snapshots -v
```

Expected: FAIL because `PolygonProvider` does not accept `http_client` and only returns provider-status evidence.

- [ ] **Step 3: Write the provider error test**

Add a test where the fake client returns this for the first endpoint:

```python
{"status": "ERROR", "error": "Invalid API key"}
```

Expected:

```python
len(evidence) == 1
evidence[0].source_type == "provider_status"
evidence[0].status == "error"
evidence[0].payload["endpoint"] == "ticker_details"
evidence[0].warnings == ["Invalid API key"]
```

- [ ] **Step 4: Run the error test to verify it fails**

Run:

```bash
/Users/shankars/Library/Python/3.9/bin/uv run pytest backend/tests/test_provider_adapters.py::test_polygon_provider_returns_error_snapshot_for_provider_warning -v
```

Expected: FAIL for the same missing implementation reason.

- [ ] **Step 5: Implement minimal Polygon provider**

Implement:

```python
BASE_URL = "https://api.polygon.io"

class PolygonProvider:
    name = "polygon"

    def __init__(
        self,
        api_key: str | None = None,
        http_client: Any | None = None,
        timeout: float = 10.0,
        end_date: date | None = None,
        lookback_days: int = 120,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("POLYGON_API_KEY")
        self.http_client = http_client or httpx
        self.timeout = timeout
        self.end_date = end_date or date.today()
        self.lookback_days = lookback_days
```

Add `_request(path, params)`, provider warning detection, numeric helpers, moving average helpers, and normalization for:

- `market`: ticker details plus stock snapshot result
- `technicals`: daily aggregate bars and summary metrics
- `options`: first option-chain snapshot rows

- [ ] **Step 6: Run provider tests**

Run:

```bash
/Users/shankars/Library/Python/3.9/bin/uv run pytest backend/tests/test_provider_adapters.py -v
```

Expected: all provider adapter tests pass.

- [ ] **Step 7: Run Ruff for changed backend files**

Run:

```bash
/Users/shankars/Library/Python/3.9/bin/uv run ruff check backend/paisapal/providers/polygon.py backend/tests/test_provider_adapters.py
```

Expected: `All checks passed!`

- [ ] **Step 8: Commit provider implementation**

Run:

```bash
git add backend/paisapal/providers/polygon.py backend/tests/test_provider_adapters.py
git commit -m "feat: fetch Polygon evidence"
```

## Task 2: Documentation and Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README**

Add that `POLYGON_API_KEY` enables Polygon stock snapshot, daily bars, technical summary, and options-chain evidence.

- [ ] **Step 2: Run full verification**

Run:

```bash
/Users/shankars/Library/Python/3.9/bin/uv run pytest backend/tests -q
/Users/shankars/Library/Python/3.9/bin/uv run ruff check backend
cd frontend && npm test -- --run && npm run build
```

- [ ] **Step 3: Commit README**

Run:

```bash
git add README.md
git commit -m "docs: document Polygon evidence provider"
```

## Self-Review

- Spec coverage: The plan implements the Polygon adapter, tests, documentation, and verification from the design spec.
- Placeholder scan: No placeholders remain.
- Type consistency: The plan uses the existing `PolygonProvider.collect(ticker) -> list[EvidenceSnapshot]` adapter contract.
