from __future__ import annotations

from typing import Any
import os

from sqlalchemy.orm import Session

from paisapal.ai.prompts import build_framework_prompt
from paisapal.analysis_runs.evidence_guard import enforce_missing_evidence_ratings
from paisapal.analysis_runs.models import AnalysisRunSettings
from paisapal.analysis_runs.mock_pipeline import build_mock_report
from paisapal.db.repository import save_analysis_report, update_job_status
from paisapal.providers.base import MarketDataProvider
from paisapal.providers.alpha_vantage import AlphaVantageProvider
from paisapal.providers.fmp import FmpProvider
from paisapal.providers.mock import MockProvider
from paisapal.providers.polygon import PolygonProvider
from paisapal.providers.sec_edgar import SecEdgarProvider
from paisapal.providers.stooq import StooqProvider
from paisapal.providers.yahoo import YahooFinanceProvider


def configured_providers() -> list[MarketDataProvider]:
    if os.getenv("MARKET_DATA_MODE", "free").strip().lower() == "free":
        providers: list[MarketDataProvider] = [
            YahooFinanceProvider(),
            SecEdgarProvider(),
            StooqProvider(),
        ]
        if os.getenv("ENABLE_PAID_PROVIDER_FALLBACK", "false").strip().lower() in {
            "1",
            "true",
            "yes",
        }:
            providers.extend(_configured_paid_providers())
        return providers
    return _configured_paid_providers() or [MockProvider()]


def _configured_paid_providers() -> list[MarketDataProvider]:
    providers: list[MarketDataProvider] = []
    for provider in [AlphaVantageProvider(), FmpProvider(), PolygonProvider()]:
        if provider.api_key:
            providers.append(provider)
    return providers


class AnalysisOrchestrator:
    def __init__(
        self,
        providers: list[MarketDataProvider] | None = None,
        ai_client: Any | None = None,
        use_live_ai: bool = False,
    ) -> None:
        self.providers = providers or [MockProvider()]
        self.ai_client = ai_client
        self.use_live_ai = use_live_ai

    def run_job(self, session: Session, job) -> None:
        try:
            update_job_status(session, job.id, "fetching_market_data")
            evidence = []
            for provider in self.providers:
                evidence.extend(provider.collect(job.ticker))

            update_job_status(session, job.id, "running_gpt_analysis")
            if self.use_live_ai and self.ai_client is not None:
                settings = AnalysisRunSettings(
                    account_size=job.run.account_size,
                    risk_percent=job.run.risk_percent,
                    max_dollar_risk=job.run.max_dollar_risk,
                    notes=job.run.notes,
                )
                prompt = build_framework_prompt(job.ticker, settings, evidence)
                report = self.ai_client.analyze(prompt).model_dump()
            else:
                report = build_mock_report(job.ticker)
            report = enforce_missing_evidence_ratings(report, evidence)
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
