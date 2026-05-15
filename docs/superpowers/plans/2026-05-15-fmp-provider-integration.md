# FMP Provider Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a tested Financial Modeling Prep provider that supplies fundamentals, financials, ratios, health scores, and earnings evidence for live ticker analysis.

**Architecture:** Follow the Alpha Vantage adapter pattern: injectable HTTP client, compact normalized `EvidenceSnapshot` payloads, key-aware missing snapshots, and provider error snapshots. The existing `configured_providers()` factory already instantiates `FmpProvider`, so this slice mostly replaces the FMP skeleton.

**Tech Stack:** Python 3.12, `httpx`, pytest, Ruff, FastAPI provider adapter boundary, Financial Modeling Prep stable API.

---

## Files

- Modify: `backend/paisapal/providers/fmp.py` - implement real FMP HTTP collection and normalization.
- Modify: `backend/tests/test_provider_adapters.py` - add FMP provider behavior tests with fake HTTP client.
- Modify: `README.md` - document FMP evidence coverage.

## Task 1: FMP HTTP Provider

**Files:**
- Modify: `backend/tests/test_provider_adapters.py`
- Modify: `backend/paisapal/providers/fmp.py`

- [ ] **Step 1: Write the failing success test**

Add a fake FMP response/client pair and a test that calls:

```python
provider = FmpProvider(api_key="demo-key", http_client=http_client)
evidence = provider.collect("NVDA")
```

Expected evidence source types:

```python
{"fundamentals", "financials", "ratios", "earnings"}
```

Expected normalized fields:

```python
fundamentals.payload["market_cap"] == 5000000000
financials.payload["income_statements"][0]["revenue"] == 100000000
ratios.payload["ratios"][0]["gross_profit_margin"] == 0.75
earnings.payload["earnings"][0]["eps_actual"] == 1.23
```

Expected request paths:

```python
[
    "profile",
    "income-statement",
    "balance-sheet-statement",
    "cash-flow-statement",
    "ratios",
    "key-metrics",
    "financial-scores",
    "earnings",
]
```

Each request must include `symbol="NVDA"` and `apikey="demo-key"`. All requests except `profile` and `financial-scores` must include `limit`.

- [ ] **Step 2: Run the success test to verify it fails**

Run:

```bash
/Users/shankars/Library/Python/3.9/bin/uv run pytest backend/tests/test_provider_adapters.py::test_fmp_provider_collects_live_evidence_snapshots -v
```

Expected: FAIL because `FmpProvider` does not accept `http_client` and only returns provider-status evidence.

- [ ] **Step 3: Write the provider error test**

Add a test where the fake client returns:

```python
{"Error Message": "Invalid API key"}
```

Expected:

```python
len(evidence) == 1
evidence[0].source_type == "provider_status"
evidence[0].status == "error"
evidence[0].warnings == ["Invalid API key"]
```

- [ ] **Step 4: Run the error test to verify it fails**

Run:

```bash
/Users/shankars/Library/Python/3.9/bin/uv run pytest backend/tests/test_provider_adapters.py::test_fmp_provider_returns_error_snapshot_for_provider_warning -v
```

Expected: FAIL for the same missing implementation reason.

- [ ] **Step 5: Implement minimal FMP provider**

Implement:

```python
BASE_URL = "https://financialmodelingprep.com/stable"

class FmpProvider:
    name = "fmp"

    def __init__(self, api_key: str | None = None, http_client: Any | None = None, timeout: float = 10.0) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("FMP_API_KEY")
        self.http_client = http_client or httpx
        self.timeout = timeout
```

Add `_request(endpoint, ticker, limit=None)`, provider warning detection, numeric helpers, and normalization for:

- `fundamentals`: first `profile` row
- `financials`: recent income statements, balance sheets, cash flows
- `ratios`: recent ratios, key metrics, and first financial score row
- `earnings`: recent earnings rows

- [ ] **Step 6: Run provider tests**

Run:

```bash
/Users/shankars/Library/Python/3.9/bin/uv run pytest backend/tests/test_provider_adapters.py -v
```

Expected: all provider adapter tests pass.

- [ ] **Step 7: Run Ruff for changed backend files**

Run:

```bash
/Users/shankars/Library/Python/3.9/bin/uv run ruff check backend/paisapal/providers/fmp.py backend/tests/test_provider_adapters.py
```

Expected: `All checks passed!`

- [ ] **Step 8: Commit provider implementation**

Run:

```bash
git add backend/paisapal/providers/fmp.py backend/tests/test_provider_adapters.py
git commit -m "feat: fetch FMP evidence"
```

## Task 2: Documentation and Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README**

Add that `FMP_API_KEY` enables Financial Modeling Prep fundamentals, financial statements, ratios, health scores, and earnings evidence.

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
git commit -m "docs: document FMP evidence provider"
```

## Self-Review

- Spec coverage: The plan implements the FMP adapter, tests, documentation, and verification from the design spec.
- Placeholder scan: No placeholders remain.
- Type consistency: The plan uses the existing `FmpProvider.collect(ticker) -> list[EvidenceSnapshot]` adapter contract.
