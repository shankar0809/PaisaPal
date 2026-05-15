from paisapal.csv_import.parser import parse_watchlist_csv


def test_parse_watchlist_csv_accepts_valid_rows_and_normalizes_ticker():
    csv_text = """ticker,current_price,week_52_high,week_52_low,resistance,support,ma_20,ma_50,ma_200,relative_strength,sector_trend,market_trend,entry,stop_loss,target_1,target_2
msft,420,430,280,425,400,415,405,360,improving,strong,supportive,420,399,462,483
"""

    preview = parse_watchlist_csv(csv_text)

    assert len(preview.valid_rows) == 1
    assert preview.valid_rows[0].analysis_input.ticker == "MSFT"
    assert preview.errors == []


def test_parse_watchlist_csv_reports_invalid_stop_loss():
    csv_text = """ticker,current_price,week_52_high,week_52_low,resistance,support,ma_20,ma_50,ma_200,relative_strength,sector_trend,market_trend,entry,stop_loss,target_1,target_2
MSFT,420,430,280,425,400,415,405,360,improving,strong,supportive,420,430,462,483
"""

    preview = parse_watchlist_csv(csv_text)

    assert preview.valid_rows == []
    assert preview.errors[0].row_number == 2
    assert preview.errors[0].column == "stop_loss"
