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


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tickers_json: Mapped[str] = mapped_column(Text)
    account_size: Mapped[float] = mapped_column(Float)
    risk_percent: Mapped[float] = mapped_column(Float)
    max_dollar_risk: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    jobs: Mapped[list[AnalysisJob]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="AnalysisJob.id",
    )


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("analysis_runs.id"), index=True)
    ticker: Mapped[str] = mapped_column(String(20), index=True)
    status: Mapped[str] = mapped_column(String(40), default="queued", index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    run: Mapped[AnalysisRun] = relationship(back_populates="jobs")
    sources: Mapped[list[SourceSnapshot]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )
    report: Mapped[AnalysisReport | None] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
        uselist=False,
    )


class SourceSnapshot(Base):
    __tablename__ = "source_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("analysis_jobs.id"), index=True)
    ticker: Mapped[str] = mapped_column(String(20), index=True)
    provider: Mapped[str] = mapped_column(String(80), index=True)
    source_type: Mapped[str] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    label: Mapped[str] = mapped_column(String(255))
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload_json: Mapped[str] = mapped_column(Text)
    warnings_json: Mapped[str] = mapped_column(Text, default="[]")
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    job: Mapped[AnalysisJob] = relationship(back_populates="sources")


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("analysis_jobs.id"),
        index=True,
        unique=True,
    )
    ticker: Mapped[str] = mapped_column(String(20), index=True)
    company_name: Mapped[str] = mapped_column(String(255))
    current_price: Mapped[float] = mapped_column(Float)
    final_decision: Mapped[str] = mapped_column(String(50), index=True)
    confidence: Mapped[str] = mapped_column(String(30), index=True)
    technical_rating: Mapped[str] = mapped_column(String(80), index=True)
    fundamental_rating: Mapped[str] = mapped_column(String(80), index=True)
    earnings_rating: Mapped[str] = mapped_column(String(80), index=True)
    sentiment_rating: Mapped[str] = mapped_column(String(80), index=True)
    options_flow_rating: Mapped[str] = mapped_column(String(80), index=True)
    risk_reward: Mapped[float | None] = mapped_column(Float, nullable=True)
    report_json: Mapped[str] = mapped_column(Text)
    markdown_report: Mapped[str] = mapped_column(Text)
    source_summary_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
    )

    job: Mapped[AnalysisJob] = relationship(back_populates="report")
