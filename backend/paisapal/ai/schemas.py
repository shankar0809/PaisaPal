from __future__ import annotations

from paisapal.analysis_runs.models import AiReportOutput


def validate_ai_report(payload: dict) -> AiReportOutput:
    return AiReportOutput.model_validate(payload)
