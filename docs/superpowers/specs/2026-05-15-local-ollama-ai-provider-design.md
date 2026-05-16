# Local Ollama AI Provider Design

## Goal

PaisaPal should support a free local AI mode that uses Ollama for report generation while continuing to collect market evidence from Alpha Vantage, Financial Modeling Prep, and Polygon.

## User Experience

The user can set:

```bash
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:7b-instruct
```

With that configuration, the normal Run Analysis flow creates reports using the local model. The existing OpenAI path remains available with:

```bash
AI_PROVIDER=openai
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5.5
```

## Architecture

Add a provider-neutral AI client boundary with two implementations:

- `OpenAiAnalysisClient`: current Responses API implementation.
- `OllamaAnalysisClient`: local HTTP client that calls Ollama's `/api/generate` endpoint with `format: "json"` and validates the returned JSON against `AiReportOutput`.

The orchestrator continues to build the same PaisaPal framework prompt and save the same report schema. Market-data providers remain unchanged.

## Data Flow

1. The user creates an analysis run.
2. The backend collects evidence from configured market-data providers.
3. The orchestrator builds the existing framework prompt.
4. The selected AI client generates JSON matching `AiReportOutput`.
5. The repository stores the report and source snapshots exactly as it does today.

## Configuration

`AI_PROVIDER` selects the AI backend:

- `openai`: requires `OPENAI_API_KEY`; uses `OPENAI_MODEL` or the default.
- `ollama`: requires a reachable Ollama server; uses `OLLAMA_MODEL` or the default.

Provider status should report the selected AI provider and whether it is configured. Market-data readiness should still require at least one configured market-data provider for live analysis.

## Error Handling

If Ollama is not running, the job fails with a clear message telling the user to start Ollama. If the local model returns invalid JSON, the client retries once with a correction prompt. If validation still fails, the job fails and records the validation error.

## Testing

Backend tests should cover:

- AI client factory selection for OpenAI and Ollama.
- Ollama JSON response parsing and validation.
- Ollama invalid JSON retry behavior.
- `/api/provider-status` in local AI mode.
- `run_analysis` wiring to the selected AI client.

No frontend changes are required for the first implementation because the normal Run Analysis button can use the configured AI provider.
