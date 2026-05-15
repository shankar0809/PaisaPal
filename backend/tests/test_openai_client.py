from paisapal.ai.client import OpenAiAnalysisClient

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
