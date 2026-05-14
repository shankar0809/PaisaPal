from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from paisapal.analysis.rules import analyze
from paisapal.csv_import.parser import parse_watchlist_csv
from paisapal.db.base import Base
from paisapal.db.repository import create_import_batch, get_latest_watchlist


def test_create_import_batch_saves_snapshot():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    csv_text = """ticker,current_price,week_52_high,week_52_low,resistance,support,ma_20,ma_50,ma_200,relative_strength,sector_trend,market_trend,entry,stop_loss,target_1,target_2
MSFT,420,430,280,425,400,415,405,360,improving,strong,supportive,420,399,462,483
"""
    preview = parse_watchlist_csv(csv_text)
    batch = create_import_batch(session, "sample.csv", preview.valid_rows, analyze)

    rows = get_latest_watchlist(session)

    assert batch.filename == "sample.csv"
    assert rows[0].ticker == "MSFT"
    assert rows[0].final_decision in {"Watchlist", "Buy / Enter", "Avoid", "Wait for Pullback"}
