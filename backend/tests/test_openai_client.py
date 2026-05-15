from paisapal.ai.client import OpenAiAnalysisClient


class FakeResponses:
    def create(self, **kwargs):
        self.kwargs = kwargs
        return type(
            "Response",
            (),
            {
                "output_text": """
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
""",
            },
        )()


class FakeOpenAI:
    def __init__(self):
        self.responses = FakeResponses()


def test_openai_analysis_client_validates_json_output():
    fake = FakeOpenAI()
    client = OpenAiAnalysisClient(openai_client=fake, model="gpt-5.5")

    report = client.analyze("prompt")

    assert report.ticker == "NVDA"
    assert fake.responses.kwargs["model"] == "gpt-5.5"
