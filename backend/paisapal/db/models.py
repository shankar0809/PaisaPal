from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paisapal.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    valid_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)

    ticker_inputs: Mapped[list[TickerInput]] = relationship(back_populates="batch")


class TickerInput(Base):
    __tablename__ = "ticker_inputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("import_batches.id"))
    ticker: Mapped[str] = mapped_column(String(20), index=True)
    input_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    batch: Mapped[ImportBatch] = relationship(back_populates="ticker_inputs")
    snapshots: Mapped[list[AnalysisSnapshot]] = relationship(back_populates="ticker_input")


class AnalysisSnapshot(Base):
    __tablename__ = "analysis_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker_input_id: Mapped[int] = mapped_column(ForeignKey("ticker_inputs.id"))
    ticker: Mapped[str] = mapped_column(String(20), index=True)
    current_price: Mapped[float] = mapped_column(Float)
    final_decision: Mapped[str] = mapped_column(String(50), index=True)
    confidence: Mapped[str] = mapped_column(String(20), index=True)
    technical_rating: Mapped[str] = mapped_column(String(80), index=True)
    fundamental_rating: Mapped[str] = mapped_column(String(80), index=True)
    sentiment_rating: Mapped[str] = mapped_column(String(80), index=True)
    options_flow_rating: Mapped[str] = mapped_column(String(80), index=True)
    risk_reward: Mapped[float | None] = mapped_column(Float, nullable=True)
    report_json: Mapped[str] = mapped_column(Text)
    markdown_report: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
    )

    ticker_input: Mapped[TickerInput] = relationship(back_populates="snapshots")
