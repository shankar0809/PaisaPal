import type {
  AnalysisRun,
  HistoryRow,
  ImportCommit,
  ImportPreview,
  ProviderStatus,
  TickerReport,
  WatchlistRow
} from "../types";

export type CreateAnalysisRunPayload = {
  tickers: string[];
  account_size: number;
  risk_percent: number;
  max_dollar_risk: number | null;
  notes: string;
};

async function errorFromResponse(response: Response, fallback: string): Promise<Error> {
  const message = await response.text();
  return new Error(message || fallback);
}

export async function previewImport(file: File): Promise<ImportPreview> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch("/api/import/preview", { method: "POST", body: formData });
  if (!response.ok) throw new Error("Import preview failed");
  return response.json();
}

export async function commitImport(previewId: string): Promise<ImportCommit> {
  const response = await fetch("/api/import/commit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ preview_id: previewId })
  });
  if (!response.ok) throw new Error("Import commit failed");
  return response.json();
}

export async function fetchWatchlist(params = new URLSearchParams()): Promise<WatchlistRow[]> {
  const query = params.toString();
  const response = await fetch(`/api/watchlist${query ? `?${query}` : ""}`);
  if (!response.ok) throw new Error("Failed to load watchlist");
  return response.json();
}

export async function fetchTickerReport(ticker: string): Promise<TickerReport> {
  const response = await fetch(`/api/tickers/${encodeURIComponent(ticker)}`);
  if (!response.ok) throw new Error("Failed to load ticker report");
  return response.json();
}

export async function fetchTickerHistory(ticker: string): Promise<HistoryRow[]> {
  const response = await fetch(`/api/tickers/${encodeURIComponent(ticker)}/history`);
  if (!response.ok) throw new Error("Failed to load ticker history");
  return response.json();
}

export async function createAnalysisRun(payload: CreateAnalysisRunPayload): Promise<AnalysisRun> {
  const response = await fetch("/api/analysis-runs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) throw await errorFromResponse(response, "Failed to create analysis run");
  return response.json();
}

export async function fetchAnalysisRun(runId: number): Promise<AnalysisRun> {
  const response = await fetch(`/api/analysis-runs/${runId}`);
  if (!response.ok) throw await errorFromResponse(response, "Failed to load analysis run");
  return response.json();
}

export async function runMockAnalysis(runId: number): Promise<AnalysisRun> {
  const response = await fetch(`/api/analysis-runs/${runId}/run-mock`, { method: "POST" });
  if (!response.ok) throw await errorFromResponse(response, "Failed to run mock analysis");
  return response.json();
}

export async function fetchProviderStatus(): Promise<ProviderStatus[]> {
  const response = await fetch("/api/provider-status");
  if (!response.ok) throw await errorFromResponse(response, "Failed to load provider status");
  return response.json();
}
