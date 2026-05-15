from __future__ import annotations

import csv
from io import StringIO

from pydantic import BaseModel

from paisapal.analysis.models import (
    AnalysisInput,
    ContextInput,
    FundamentalScores,
    OptionsFlow,
    SentimentInput,
    TradePlan,
    VcpInput,
)
from paisapal.csv_import.schema import BOOLEAN_COLUMNS, REQUIRED_COLUMNS, SCORE_COLUMNS


class CsvValidationIssue(BaseModel):
    row_number: int
    column: str
    message: str


class ValidCsvRow(BaseModel):
    row_number: int
    raw: dict[str, str]
    analysis_input: AnalysisInput


class ParsePreview(BaseModel):
    valid_rows: list[ValidCsvRow]
    errors: list[CsvValidationIssue]
    warnings: list[CsvValidationIssue]


def _parse_float(
    value: str, row_number: int, column: str, errors: list[CsvValidationIssue]
) -> float:
    try:
        parsed = float(value)
    except ValueError:
        errors.append(
            CsvValidationIssue(row_number=row_number, column=column, message="must be a number")
        )
        return 0.0
    if parsed <= 0:
        errors.append(
            CsvValidationIssue(row_number=row_number, column=column, message="must be positive")
        )
    return parsed


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "yes", "1", "y"}


def _parse_score(
    value: str, row_number: int, column: str, errors: list[CsvValidationIssue]
) -> int:
    if value == "":
        return 3
    try:
        parsed = int(value)
    except ValueError:
        errors.append(
            CsvValidationIssue(
                row_number=row_number, column=column, message="must be an integer from 1 to 5"
            )
        )
        return 3
    if parsed < 1 or parsed > 5:
        errors.append(
            CsvValidationIssue(row_number=row_number, column=column, message="must be between 1 and 5")
        )
    return parsed


def parse_watchlist_csv(csv_text: str) -> ParsePreview:
    reader = csv.DictReader(StringIO(csv_text))
    headers = {header.strip() for header in (reader.fieldnames or [])}
    valid_rows: list[ValidCsvRow] = []
    errors: list[CsvValidationIssue] = []
    warnings: list[CsvValidationIssue] = []

    missing = REQUIRED_COLUMNS - headers
    for column in sorted(missing):
        errors.append(
            CsvValidationIssue(row_number=1, column=column, message="required column is missing")
        )

    known = REQUIRED_COLUMNS | BOOLEAN_COLUMNS | SCORE_COLUMNS | {
        "market_cap",
        "upcoming_catalyst",
        "analyst_sentiment",
        "news_sentiment",
        "short_interest_signal",
        "insider_activity_signal",
        "sector_sentiment",
        "call_volume",
        "put_volume",
        "call_open_interest",
        "put_open_interest",
        "iv_rank",
        "iv_percentile",
        "expected_move",
    }
    for column in sorted(headers - known):
        warnings.append(CsvValidationIssue(row_number=1, column=column, message="unknown column ignored"))

    if missing:
        return ParsePreview(valid_rows=[], errors=errors, warnings=warnings)

    for row_number, raw_row in enumerate(reader, start=2):
        row = {key.strip(): (value or "").strip() for key, value in raw_row.items() if key}
        row_errors: list[CsvValidationIssue] = []
        ticker = row["ticker"].upper()
        if not ticker:
            row_errors.append(
                CsvValidationIssue(row_number=row_number, column="ticker", message="must not be empty")
            )

        current_price = _parse_float(row["current_price"], row_number, "current_price", row_errors)
        entry = _parse_float(row["entry"], row_number, "entry", row_errors)
        stop_loss = _parse_float(row["stop_loss"], row_number, "stop_loss", row_errors)
        target_1 = _parse_float(row["target_1"], row_number, "target_1", row_errors)
        target_2 = _parse_float(row["target_2"], row_number, "target_2", row_errors)

        if stop_loss >= entry:
            row_errors.append(
                CsvValidationIssue(row_number=row_number, column="stop_loss", message="must be below entry")
            )
        if target_1 <= entry:
            row_errors.append(
                CsvValidationIssue(row_number=row_number, column="target_1", message="must be above entry")
            )
        if target_2 <= entry:
            row_errors.append(
                CsvValidationIssue(row_number=row_number, column="target_2", message="must be above entry")
            )

        if row_errors:
            errors.extend(row_errors)
            continue

        analysis_input = AnalysisInput(
            ticker=ticker,
            current_price=current_price,
            context=ContextInput(
                week_52_high=_parse_float(row["week_52_high"], row_number, "week_52_high", row_errors),
                week_52_low=_parse_float(row["week_52_low"], row_number, "week_52_low", row_errors),
                resistance=_parse_float(row["resistance"], row_number, "resistance", row_errors),
                support=_parse_float(row["support"], row_number, "support", row_errors),
                ma_20=_parse_float(row["ma_20"], row_number, "ma_20", row_errors),
                ma_50=_parse_float(row["ma_50"], row_number, "ma_50", row_errors),
                ma_200=_parse_float(row["ma_200"], row_number, "ma_200", row_errors),
                relative_strength=row["relative_strength"],
                sector_trend=row["sector_trend"],
                market_trend=row["market_trend"],
                upcoming_catalyst=row.get("upcoming_catalyst", ""),
                market_cap=row.get("market_cap", ""),
            ),
            trade_plan=TradePlan(
                entry=entry,
                stop_loss=stop_loss,
                target_1=target_1,
                target_2=target_2,
            ),
            vcp=VcpInput(
                strong_prior_uptrend=_parse_bool(row.get("vcp_strong_prior_uptrend", "")),
                above_rising_50_day=_parse_bool(row.get("vcp_above_rising_50_day", "")),
                above_rising_200_day=_parse_bool(row.get("vcp_above_rising_200_day", "")),
                relative_strength_improving=_parse_bool(
                    row.get("vcp_relative_strength_improving", "")
                ),
                orderly_consolidation=_parse_bool(row.get("vcp_orderly_consolidation", "")),
                smaller_pullbacks=_parse_bool(row.get("vcp_smaller_pullbacks", "")),
                volume_drying_up=_parse_bool(row.get("vcp_volume_drying_up", "")),
                tightening_near_resistance=_parse_bool(
                    row.get("vcp_tightening_near_resistance", "")
                ),
                clear_pivot=_parse_bool(row.get("vcp_clear_pivot", "")),
                strong_breakout_volume=_parse_bool(row.get("vcp_strong_breakout_volume", "")),
            ),
            fundamentals=FundamentalScores(
                revenue_growth=_parse_score(
                    row.get("fund_revenue_growth", ""), row_number, "fund_revenue_growth", row_errors
                ),
                eps_growth=_parse_score(
                    row.get("fund_eps_growth", ""), row_number, "fund_eps_growth", row_errors
                ),
                gross_margin=_parse_score(
                    row.get("fund_gross_margin", ""), row_number, "fund_gross_margin", row_errors
                ),
                operating_margin=_parse_score(
                    row.get("fund_operating_margin", ""), row_number, "fund_operating_margin", row_errors
                ),
                free_cash_flow=_parse_score(
                    row.get("fund_free_cash_flow", ""), row_number, "fund_free_cash_flow", row_errors
                ),
                balance_sheet=_parse_score(
                    row.get("fund_balance_sheet", ""), row_number, "fund_balance_sheet", row_errors
                ),
                valuation=_parse_score(
                    row.get("fund_valuation", ""), row_number, "fund_valuation", row_errors
                ),
                segment_strength=_parse_score(
                    row.get("fund_segment_strength", ""), row_number, "fund_segment_strength", row_errors
                ),
                guidance=_parse_score(
                    row.get("fund_guidance", ""), row_number, "fund_guidance", row_errors
                ),
                capital_return=_parse_score(
                    row.get("fund_capital_return", ""), row_number, "fund_capital_return", row_errors
                ),
            ),
            sentiment=SentimentInput(
                analyst_sentiment=row.get("analyst_sentiment", "neutral"),
                news_sentiment=row.get("news_sentiment", "neutral"),
                short_interest_signal=row.get("short_interest_signal", "neutral"),
                insider_activity_signal=row.get("insider_activity_signal", "neutral"),
                sector_sentiment=row.get("sector_sentiment", "neutral"),
                stock_rallied_sharply=_parse_bool(row.get("stock_rallied_sharply", "")),
                call_heavy_options=_parse_bool(row.get("call_heavy_options", "")),
                valuation_elevated=_parse_bool(row.get("valuation_elevated", "")),
                earnings_near=_parse_bool(row.get("earnings_near", "")),
            ),
            options_flow=OptionsFlow(
                call_volume=int(float(row.get("call_volume") or 0)),
                put_volume=int(float(row.get("put_volume") or 0)),
                call_open_interest=int(float(row.get("call_open_interest") or 0)),
                put_open_interest=int(float(row.get("put_open_interest") or 0)),
                iv_rank=float(row["iv_rank"]) if row.get("iv_rank") else None,
                iv_percentile=float(row["iv_percentile"]) if row.get("iv_percentile") else None,
                expected_move=float(row["expected_move"]) if row.get("expected_move") else None,
            ),
        )
        if row_errors:
            errors.extend(row_errors)
            continue
        valid_rows.append(ValidCsvRow(row_number=row_number, raw=row, analysis_input=analysis_input))

    return ParsePreview(valid_rows=valid_rows, errors=errors, warnings=warnings)
