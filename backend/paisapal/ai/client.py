from __future__ import annotations

import json
import os
from json import JSONDecodeError
from typing import Any

import httpx
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


class OllamaAnalysisClient:
    def __init__(
        self,
        http_client: Any | None = None,
        base_url: str | None = None,
        model: str | None = None,
        max_retries: int = 1,
        timeout: float = 600,
    ) -> None:
        self.http_client = http_client or httpx.Client()
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
        self.max_retries = max_retries
        self.timeout = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", timeout))

    def analyze(self, prompt: str) -> AiReportOutput:
        last_error: Exception | None = None
        current_prompt = prompt
        for _attempt in range(self.max_retries + 1):
            try:
                response = self.http_client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": _ollama_prompt(current_prompt),
                        "format": AiReportOutput.model_json_schema(),
                        "options": {"temperature": 0},
                        "stream": False,
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()
            except httpx.RequestError as exc:
                raise RuntimeError(
                    "Ollama is not reachable. Start Ollama and confirm "
                    f"{self.base_url}/api/generate is available. Details: {exc}"
                ) from exc

            try:
                payload = json.loads(response.json().get("response", ""))
                return validate_ai_report(payload)
            except (JSONDecodeError, ValidationError) as exc:
                last_error = exc
                current_prompt = (
                    f"{prompt}\n\nPrevious response failed validation: {exc}\n"
                    "Return only corrected JSON matching the required schema."
                )

        if last_error is not None:
            raise last_error
        raise RuntimeError("Ollama analysis failed without a validation error")


def _ollama_prompt(prompt: str) -> str:
    schema = json.dumps(AiReportOutput.model_json_schema())
    return (
        f"{prompt}\n\n"
        "Return only one JSON object. Do not include markdown fences, prose, or extra keys.\n"
        "Every required field must be present and must use the exact JSON types from this schema.\n"
        f"AiReportOutput JSON schema: {schema}"
    )


def selected_ai_provider() -> str:
    provider = os.getenv("AI_PROVIDER", "openai").strip().lower()
    return provider if provider in {"openai", "ollama"} else "openai"


def is_ai_configured() -> bool:
    if selected_ai_provider() == "ollama":
        return bool(os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct"))
    return bool(os.getenv("OPENAI_API_KEY"))


def build_analysis_client() -> OpenAiAnalysisClient | OllamaAnalysisClient | None:
    if not is_ai_configured():
        return None
    if selected_ai_provider() == "ollama":
        return OllamaAnalysisClient()
    return OpenAiAnalysisClient()


def _ai_report_json_schema_format() -> dict:
    return {
        "type": "json_schema",
        "name": "ai_report_output",
        "strict": False,
        "schema": AiReportOutput.model_json_schema(),
    }
