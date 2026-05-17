from __future__ import annotations

import csv
from io import StringIO
from typing import Any

import httpx
from paisapal.providers.base import EvidenceSnapshot, redact_url_secrets

BASE_URL = "https://stooq.com/q/d/l/"


class StooqProvider:
    name = "stooq"

    def __init__(self, http_client: Any | None = None, timeout: float = 10.0) -> None:
        self.http_client = http_client or httpx
        self.timeout = timeout

    def collect(self, ticker: str) -> list[EvidenceSnapshot]:
        try:
            rows = self._request_direct_csv(ticker)
            if not rows:
                rows = self._request_via_datareader(ticker)
            if not rows:
                return [self._error_snapshot(ticker, "Stooq response did not include rows")]
        except Exception as exc:
            return [self._error_snapshot(ticker, str(exc))]

        closes = [row["close"] for row in rows if row["close"] is not None]
        highs = [row["high"] for row in rows if row["high"] is not None]
        lows = [row["low"] for row in rows if row["low"] is not None]
        volumes = [row["volume"] for row in rows if row["volume"] is not None]
        latest = rows[-1]
        return [
            EvidenceSnapshot(
                provider=self.name,
                source_type="market",
                status="fresh",
                label="Stooq daily quote",
                payload={
                    "ticker": ticker.upper(),
                    "session": {
                        "price": latest["close"],
                        "previous_close": rows[-2]["close"] if len(rows) > 1 else None,
                    },
                },
                url=BASE_URL,
            ),
            EvidenceSnapshot(
                provider=self.name,
                source_type="technicals",
                status="fresh",
                label="Stooq daily bars",
                payload={
                    "ticker": ticker.upper(),
                    "latest_close": closes[-1] if closes else None,
                    "sma_20": _moving_average(closes, 20),
                    "sma_50": _moving_average(closes, 50),
                    "range_high": max(highs) if highs else None,
                    "range_low": min(lows) if lows else None,
                    "average_volume": round(sum(volumes) / len(volumes)) if volumes else None,
                    "bars": rows,
                },
                url=BASE_URL,
            ),
        ]

    def _request_direct_csv(self, ticker: str) -> list[dict[str, Any]]:
        stooq_symbol = get_stooq_symbol(ticker)
        response = self.http_client.get(
            BASE_URL,
            params={"s": stooq_symbol, "i": "d"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        reader = csv.DictReader(StringIO(response.text))
        rows = []
        for row in reader:
            if row.get("Close") in {None, "No data"}:
                continue
            rows.append(
                {
                    "date": row.get("Date"),
                    "open": _float_or_none(row.get("Open")),
                    "high": _float_or_none(row.get("High")),
                    "low": _float_or_none(row.get("Low")),
                    "close": _float_or_none(row.get("Close")),
                    "volume": _int_or_none(row.get("Volume")),
                }
            )
        return rows

    def _request_via_datareader(self, ticker: str) -> list[dict[str, Any]]:
        try:
            from pandas_datareader import data as pdr
        except ImportError:
            return []

        candidates = [ticker.upper(), get_stooq_symbol(ticker)]
        for symbol in candidates:
            try:
                frame = pdr.DataReader(symbol, "stooq")
            except Exception:
                continue
            rows = _frame_to_rows(frame)
            if rows:
                return rows
        return []

    def _error_snapshot(self, ticker: str, warning: str) -> EvidenceSnapshot:
        return EvidenceSnapshot(
            provider=self.name,
            source_type="provider_status",
            status="error",
            label="Stooq daily CSV",
            payload={"ticker": ticker.upper()},
            url=BASE_URL,
            warnings=[redact_url_secrets(warning)],
        )


def get_stooq_symbol(symbol: str) -> str:
    symbol = symbol.lower().strip()
    if "." not in symbol:
        symbol = f"{symbol}.us"
    return symbol


def _frame_to_rows(frame: Any) -> list[dict[str, Any]]:
    if not hasattr(frame, "sort_index") or not hasattr(frame, "reset_index"):
        return []
    try:
        from pandas import DataFrame
    except ImportError:
        return []
    if not isinstance(frame, DataFrame):
        return []
    ordered = frame.sort_index().reset_index()
    rows = []
    for _, row in ordered.iterrows():
        date_value = row.get("Date")
        rows.append(
            {
                "date": date_value.isoformat() if hasattr(date_value, "isoformat") else date_value,
                "open": _float_or_none(row.get("Open")),
                "high": _float_or_none(row.get("High")),
                "low": _float_or_none(row.get("Low")),
                "close": _float_or_none(row.get("Close")),
                "volume": _int_or_none(row.get("Volume")),
            }
        )
    return rows


def _moving_average(values: list[float], window: int) -> float | None:
    if len(values) < window:
        return None
    return round(sum(values[-window:]) / window, 4)


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None
