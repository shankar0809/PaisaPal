from paisapal.analysis.models import (
    AnalysisInput,
    ContextInput,
    FundamentalScores,
    OptionsFlow,
    TradePlan,
    VcpInput,
)
from paisapal.analysis.report import build_report_payload, render_markdown
from paisapal.analysis.rules import analyze


def strong_input() -> AnalysisInput:
    return AnalysisInput(
        ticker="MSFT",
        current_price=420,
        context=ContextInput(
            week_52_high=430,
            week_52_low=280,
            resistance=425,
            support=400,
            ma_20=415,
            ma_50=405,
            ma_200=360,
            relative_strength="improving",
            sector_trend="strong",
            market_trend="supportive",
            upcoming_catalyst="",
            market_cap="3T",
        ),
        trade_plan=TradePlan(entry=420, stop_loss=399, target_1=462, target_2=483),
        vcp=VcpInput(
            strong_prior_uptrend=True,
            above_rising_50_day=True,
            above_rising_200_day=True,
            relative_strength_improving=True,
            orderly_consolidation=True,
            smaller_pullbacks=True,
            volume_drying_up=True,
            tightening_near_resistance=True,
            clear_pivot=True,
            strong_breakout_volume=False,
        ),
        fundamentals=FundamentalScores(
            revenue_growth=5,
            eps_growth=5,
            gross_margin=4,
            operating_margin=4,
            free_cash_flow=5,
            balance_sheet=4,
            valuation=3,
            segment_strength=4,
            guidance=4,
            capital_return=3,
        ),
        options_flow=OptionsFlow(
            call_volume=10000,
            put_volume=7000,
            call_open_interest=20000,
            put_open_interest=15000,
        ),
    )


def test_analyze_returns_buy_for_strong_setup():
    result = analyze(strong_input(), account_size=100000, risk_percent=0.5)

    assert result.ticker == "MSFT"
    assert result.vcp_score == 9
    assert result.vcp_rating == "High-quality VCP"
    assert result.fundamental_score == 41
    assert result.risk_reward == 2.0
    assert result.position_size == 23
    assert result.final_decision == "Buy / Enter"


def test_analyze_avoids_when_stop_is_invalid():
    data = strong_input()
    invalid = data.model_copy(
        update={"trade_plan": TradePlan(entry=420, stop_loss=430, target_1=462, target_2=483)}
    )

    result = analyze(invalid, account_size=100000, risk_percent=0.5)

    assert result.final_decision == "Avoid"
    assert "stop_loss must be below entry" in result.warnings


def test_render_markdown_includes_vcp_summary_and_stage():
    data = strong_input()
    result = analyze(data, account_size=100000, risk_percent=0.5)

    markdown = render_markdown(data, result)
    payload = build_report_payload(data, result)

    assert "- Ticker: MSFT" in markdown
    assert "- VCP Score: 9" in markdown
    assert "- Stage: Stage 2" in markdown
    assert "- Tech Output: Strong VCP watchlist candidate" in markdown
    assert payload["analysis"]["vcp_summary"]["vcp_score"] == 9
    assert payload["analysis"]["vcp_summary"]["vcp_stage"] == "Stage 2"
