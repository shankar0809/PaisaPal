from __future__ import annotations

from sqlalchemy.orm import Session

from paisapal.analysis_runs.mock_pipeline import build_mock_report
from paisapal.db.repository import save_analysis_report, update_job_status
from paisapal.providers.base import MarketDataProvider
from paisapal.providers.mock import MockProvider


class AnalysisOrchestrator:
    def __init__(self, providers: list[MarketDataProvider] | None = None) -> None:
        self.providers = providers or [MockProvider()]

    def run_job(self, session: Session, job) -> None:
        try:
            update_job_status(session, job.id, "fetching_market_data")
            evidence = []
            for provider in self.providers:
                evidence.extend(provider.collect(job.ticker))

            update_job_status(session, job.id, "running_gpt_analysis")
            report = build_mock_report(job.ticker)
            report["source_summary"] = [
                {
                    "provider": item.provider,
                    "retrieved_at": item.retrieved_at,
                    "status": item.status,
                    "label": item.label,
                    "url": item.url,
                    "warnings": item.warnings,
                }
                for item in evidence
            ]
            save_analysis_report(
                session,
                job_id=job.id,
                report=report,
                source_snapshots=[item.as_source_row() for item in evidence],
            )
        except Exception as exc:
            update_job_status(session, job.id, "failed", str(exc))
