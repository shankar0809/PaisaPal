from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from paisapal.ai.schemas import validate_ai_report
from paisapal.analysis_runs.models import AiReportOutput


class OpenAiAnalysisClient:
    def __init__(self, openai_client: Any | None = None, model: str | None = None) -> None:
        self.client = openai_client or OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.5")

    def analyze(self, prompt: str) -> AiReportOutput:
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            tools=[{"type": "web_search_preview"}],
        )
        payload = json.loads(response.output_text)
        return validate_ai_report(payload)
