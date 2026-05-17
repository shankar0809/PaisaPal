import httpx
import pytest

from paisapal.ai.client import OllamaAnalysisClient, OpenAiAnalysisClient, build_analysis_client

VALID_REPORT_JSON = """
{
  "ticker": "NVDA",
  "company_name": "NVIDIA Corporation",
  "current_price": 211.5,
  "final_classification": "Watchlist",
  "confidence": "Medium",
  "technical_rating": "Constructive",
  "vcp_rating": "Watchlist candidate",
  "fundamental_rating": "Very strong",
  "earnings_rating": "Strong",
  "sentiment_rating": "Bullish but crowded",
  "options_flow_rating": "Call-heavy",
  "risk_reward": 2.1,
  "entry_zones": [],
  "stop_zones": [],
  "target_zones": [],
  "position_sizing": [],
  "bullish_factors": [],
  "bearish_risks": [],
  "data_warnings": [],
  "source_summary": [],
  "markdown_report": "# NVIDIA Corporation (NVDA) - Stock Analysis Report"
}
"""


class FakeResponses:
    def __init__(self, outputs=None):
        self.outputs = outputs or [VALID_REPORT_JSON]
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        self.kwargs = kwargs
        return type(
            "Response",
            (),
            {"output_text": self.outputs.pop(0)},
        )()


class FakeOpenAI:
    def __init__(self, outputs=None):
        self.responses = FakeResponses(outputs)


def test_openai_analysis_client_validates_json_output():
    fake = FakeOpenAI()
    client = OpenAiAnalysisClient(openai_client=fake, model="gpt-5.5")

    report = client.analyze("prompt")

    assert report.ticker == "NVDA"
    assert fake.responses.kwargs["model"] == "gpt-5.5"


def test_openai_analysis_client_requests_json_schema_output():
    fake = FakeOpenAI()
    client = OpenAiAnalysisClient(openai_client=fake, model="gpt-5.5")

    client.analyze("prompt")

    text_format = fake.responses.kwargs["text"]["format"]
    assert text_format["type"] == "json_schema"
    assert text_format["name"] == "ai_report_output"
    assert text_format["schema"]["properties"]["final_classification"]["enum"] == [
        "Buy / Enter",
        "Watchlist",
        "Wait for Pullback",
        "Avoid",
        "Reduce",
        "Exit",
    ]


def test_openai_analysis_client_retries_after_invalid_json_output():
    fake = FakeOpenAI(outputs=["not json", VALID_REPORT_JSON])
    client = OpenAiAnalysisClient(openai_client=fake, model="gpt-5.5", max_retries=1)

    report = client.analyze("prompt")

    assert report.ticker == "NVDA"
    assert len(fake.responses.calls) == 2
    assert "Previous response failed validation" in fake.responses.calls[1]["input"]


class FakeOllamaResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeHttpClient:
    def __init__(self, payloads):
        self.payloads = payloads
        self.calls = []

    def post(self, url, json, timeout):
        self.calls.append({"url": url, "json": json, "timeout": timeout})
        return FakeOllamaResponse(self.payloads.pop(0))


def test_ollama_analysis_client_validates_json_response():
    fake_http = FakeHttpClient([{"response": VALID_REPORT_JSON}])
    client = OllamaAnalysisClient(
        http_client=fake_http,
        base_url="http://127.0.0.1:11434",
        model="qwen2.5:7b-instruct",
    )

    report = client.analyze("prompt")

    assert report.ticker == "NVDA"
    assert fake_http.calls[0]["url"] == "http://127.0.0.1:11434/api/generate"
    assert fake_http.calls[0]["json"]["model"] == "qwen2.5:7b-instruct"
    assert fake_http.calls[0]["json"]["format"]["properties"]["ticker"]["type"] == "string"
    assert "AiReportOutput JSON schema" in fake_http.calls[0]["json"]["prompt"]
    assert fake_http.calls[0]["json"]["stream"] is False


def test_ollama_analysis_client_uses_extended_timeout_for_long_reports():
    fake_http = FakeHttpClient([{"response": VALID_REPORT_JSON}])
    client = OllamaAnalysisClient(http_client=fake_http, model="qwen2.5:7b-instruct")

    client.analyze("prompt")

    assert fake_http.calls[0]["timeout"] == 900


def test_ollama_analysis_client_retries_after_invalid_json_output():
    fake_http = FakeHttpClient([{"response": "not json"}, {"response": VALID_REPORT_JSON}])
    client = OllamaAnalysisClient(http_client=fake_http, model="qwen2.5:7b-instruct", max_retries=1)

    report = client.analyze("prompt")

    assert report.ticker == "NVDA"
    assert len(fake_http.calls) == 2
    assert "Previous response failed validation" in fake_http.calls[1]["json"]["prompt"]


def test_ollama_analysis_client_raises_clear_error_when_server_is_unreachable():
    class FailingHttpClient:
        def post(self, url, json, timeout):
            raise httpx.ConnectError("connection refused")

    client = OllamaAnalysisClient(http_client=FailingHttpClient(), model="qwen2.5:7b-instruct")

    with pytest.raises(RuntimeError, match="Ollama is not reachable"):
        client.analyze("prompt")


def test_build_analysis_client_selects_ollama(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")

    client = build_analysis_client()

    assert isinstance(client, OllamaAnalysisClient)
    assert client.model == "qwen2.5:7b-instruct"
