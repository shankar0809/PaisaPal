from __future__ import annotations

import json
import os
from json import JSONDecodeError
from typing import Any

from openai import OpenAI
from pydantic import ValidationError

from paisapal.ai.schemas import validate_ai_report
from paisapal.analysis_runs.models import AiReportOutput


class OpenAiAnalysisClient:
    def __init__(self, openai_client: Any | None = None, model: str | None = None, max_retries: int = 1) -> None:
        self.client = openai_client or OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.5")
        self.max_retries = max_retries

    def analyze(self, prompt: str) -> AiReportOutput:
        last_error: Exception | None = None
        current_prompt = prompt
        for _attempt in range(self.max_retries + 1):
            response = self.client.responses.create(
                model=self.model,
                input=current_prompt,
                tools=[{"type": "web_search_preview"}],
                text={"format": _ai_report_json_schema_format()},
            )
            try:
                payload = json.loads(response.output_text)
                return validate_ai_report(payload)
            except (JSONDecodeError, ValidationError) as exc:
                last_error = exc
                current_prompt = (
                    f"{prompt}\n\nPrevious response failed validation: {exc}\n"
                    "Return only corrected JSON matching the required schema."
                )

        if last_error is not None:
            raise last_error
        raise RuntimeError("OpenAI analysis failed without a validation error")


def _ai_report_json_schema_format() -> dict:
    return {
        "type": "json_schema",
        "name": "ai_report_output",
        "strict": False,
        "schema": AiReportOutput.model_json_schema(),
    }
